
import 'package:flutter/foundation.dart';
import 'package:just_audio/just_audio.dart';
import 'package:just_audio_background/just_audio_background.dart';
import '../models/models.dart';
import '../services/api_service.dart';

enum RepeatMode { off, all, one }

class PlayerProvider extends ChangeNotifier {
  final ApiService _apiService;
  final AudioPlayer _player = AudioPlayer();
  
  // Pre-resolved stream URLs — the key to instant playback
  final Map<String, String> _streamUrlCache = {};
  
  List<Song> _queue = [];
  int _currentIndex = -1;
  bool _isLoading = false;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  Song? _currentSong;
  bool _isPlaying = false;
  bool _isShuffled = false;
  RepeatMode _repeatMode = RepeatMode.off;
  String? _currentPlayId;

  PlayerProvider(this._apiService) {
    _initPlayer();
  }

  // Getters
  Song? get currentSong => _currentSong;
  bool get isPlaying => _isPlaying;
  bool get isLoading => _isLoading;
  Duration get position => _position;
  Duration get duration => _duration;
  List<Song> get queue => _queue;
  int get currentIndex => _currentIndex;
  bool get isShuffled => _isShuffled;
  RepeatMode get repeatMode => _repeatMode;
  bool get hasNext => _currentIndex < _queue.length - 1;
  bool get hasPrevious => _currentIndex > 0;
  double get progress => _duration.inSeconds > 0 
      ? _position.inSeconds / _duration.inSeconds 
      : 0.0;

  void _initPlayer() {
    _player.playerStateStream.listen((state) {
      _isPlaying = state.playing;
      if (state.processingState == ProcessingState.completed) {
        _onSongCompleted();
      }
      notifyListeners();
    });

    _player.positionStream.listen((pos) {
      _position = pos;
      notifyListeners();
    });

    _player.durationStream.listen((dur) {
      _duration = dur ?? Duration.zero;
      notifyListeners();
    });
  }

  void _onSongCompleted() {
    if (_currentPlayId != null && _currentSong != null) {
      _apiService.trackComplete(
        _currentPlayId!,
        _currentSong!.durationSeconds,
      );
      _currentPlayId = null;
    }

    if (_repeatMode == RepeatMode.one) {
      _player.seek(Duration.zero);
      _player.play();
    } else if (hasNext) {
      skipToNext();
    } else if (_repeatMode == RepeatMode.all && _queue.isNotEmpty) {
      _playIndex(0);
    }
  }

  /// Prefetch stream URLs for a list of songs so playback is instant.
  /// Call this whenever songs are displayed to the user (search results, 
  /// recommendations, queue updates).
  void prefetchSongs(List<Song> songs) {
    final ids = songs
        .where((s) => !_streamUrlCache.containsKey(s.id))
        .take(5)
        .map((s) => s.id)
        .toList();
    
    if (ids.isEmpty) return;

    // Fire backend prefetch (warms server cache)
    _apiService.prefetchSongs(ids);

    // Also resolve each URL locally in parallel
    for (final id in ids) {
      _resolveAndCache(id);
    }
  }

  Future<void> _resolveAndCache(String videoId) async {
    try {
      final data = await _apiService.getStreamUrl(videoId);
      if (data != null && data['stream_url'] != null) {
        _streamUrlCache[videoId] = data['stream_url'];
      }
    } catch (_) {
      // Silent — prefetch failure is non-critical
    }
  }

  Future<void> playSong(Song song) async {
    _trackSkipIfNeeded();

    _currentSong = song;

    // Sync _currentIndex if this song is in the queue
    final queueIdx = _queue.indexWhere((s) => s.id == song.id);
    if (queueIdx >= 0) {
      _currentIndex = queueIdx;
    }

    // Check local cache first — instant playback if cached
    final cachedUrl = _streamUrlCache[song.id];
    if (cachedUrl != null) {
      // INSTANT path — no network wait
      _isLoading = false;
      notifyListeners();
      await _startPlayback(song, cachedUrl);
    } else {
      // Fetch path — show loading, get URL
      _isLoading = true;
      notifyListeners();
      try {
        final data = await _apiService.getStreamUrl(song.id);
        if (data != null && data['stream_url'] != null) {
          _streamUrlCache[song.id] = data['stream_url'];
          await _startPlayback(song, data['stream_url']);
        }
      } catch (e) {
        debugPrint("Error playing song: $e");
      } finally {
        _isLoading = false;
        notifyListeners();
      }
    }
  }

  Future<void> _startPlayback(Song song, String streamUrl) async {
    try {
      final source = AudioSource.uri(
        Uri.parse(streamUrl),
        tag: MediaItem(
          id: song.id,
          title: song.title,
          artist: song.artist,
          artUri: Uri.parse(song.thumbnailUrl),
        ),
      );

      await _player.setAudioSource(source);
      _player.play();

      // Track play in background — don't block playback
      _apiService.trackPlay(
        videoId: song.id,
        title: song.title,
        artist: song.artist,
        duration: song.durationSeconds,
      ).then((playId) {
        _currentPlayId = playId;
      });

      // Prefetch next songs in queue
      _prefetchUpcoming();
    } catch (e) {
      debugPrint("Error starting playback: $e");
      // URL might be expired — clear cache and retry with fresh URL
      _streamUrlCache.remove(song.id);
      try {
        final data = await _apiService.getStreamUrl(song.id);
        if (data != null && data['stream_url'] != null) {
          _streamUrlCache[song.id] = data['stream_url'];
          final retrySource = AudioSource.uri(
            Uri.parse(data['stream_url']),
            tag: MediaItem(
              id: song.id,
              title: song.title,
              artist: song.artist,
              artUri: Uri.parse(song.thumbnailUrl),
            ),
          );
          await _player.setAudioSource(retrySource);
          _player.play();
        }
      } catch (retryError) {
        debugPrint("Retry also failed: $retryError");
      }
    }
  }

  Future<void> playQueue(List<Song> songs, {int startIndex = 0}) async {
    _queue = List.from(songs);
    _currentIndex = startIndex;

    // Immediately prefetch all queue songs
    prefetchSongs(songs);

    if (_queue.isNotEmpty && startIndex < _queue.length) {
      await playSong(_queue[startIndex]);
    }
  }

  Future<void> addToQueue(Song song) async {
    _queue.add(song);
    // Prefetch the added song
    if (!_streamUrlCache.containsKey(song.id)) {
      _resolveAndCache(song.id);
    }
    notifyListeners();
  }

  Future<void> playNext(Song song) async {
    if (_currentIndex >= 0 && _currentIndex < _queue.length - 1) {
      _queue.insert(_currentIndex + 1, song);
    } else {
      _queue.add(song);
    }
    // Prefetch immediately
    if (!_streamUrlCache.containsKey(song.id)) {
      _resolveAndCache(song.id);
    }
    notifyListeners();
  }

  Future<void> togglePlay() async {
    if (_isPlaying) {
      await _player.pause();
    } else {
      await _player.play();
    }
  }
  
  Future<void> seek(Duration position) async {
    await _player.seek(position);
  }

  Future<void> skipToNext() async {
    _trackSkipIfNeeded();
    if (hasNext) {
      _playIndex(_currentIndex + 1);
    } else if (_repeatMode == RepeatMode.all && _queue.isNotEmpty) {
      _playIndex(0);
    }
  }

  Future<void> skipToPrevious() async {
    if (_position.inSeconds > 3) {
      await _player.seek(Duration.zero);
      return;
    }
    _trackSkipIfNeeded();
    if (hasPrevious) {
      _playIndex(_currentIndex - 1);
    }
  }

  void toggleShuffle() {
    _isShuffled = !_isShuffled;
    if (_isShuffled && _queue.length > 1) {
      final current = _currentIndex >= 0 ? _queue[_currentIndex] : null;
      _queue.shuffle();
      if (current != null) {
        _queue.remove(current);
        _queue.insert(0, current);
        _currentIndex = 0;
      }
    }
    notifyListeners();
  }

  void toggleRepeat() {
    switch (_repeatMode) {
      case RepeatMode.off:
        _repeatMode = RepeatMode.all;
        break;
      case RepeatMode.all:
        _repeatMode = RepeatMode.one;
        break;
      case RepeatMode.one:
        _repeatMode = RepeatMode.off;
        break;
    }
    notifyListeners();
  }

  Future<void> _playIndex(int index) async {
    if (index >= 0 && index < _queue.length) {
      _currentIndex = index;
      await playSong(_queue[index]);
    }
  }

  void _trackSkipIfNeeded() {
    if (_currentPlayId != null && _currentSong != null && _isPlaying) {
      _apiService.trackSkip(_currentPlayId!, _position.inSeconds);
      _currentPlayId = null;
    }
  }

  void _prefetchUpcoming() {
    if (_currentIndex >= 0 && _currentIndex < _queue.length - 1) {
      final upcoming = _queue
          .skip(_currentIndex + 1)
          .take(3)
          .toList();
      if (upcoming.isNotEmpty) {
        prefetchSongs(upcoming);
      }
    }
  }
  
  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }
}
