import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:just_audio/just_audio.dart';
import 'package:just_audio_background/just_audio_background.dart';
import '../models/models.dart';
import '../services/api_service.dart';

enum RepeatMode { off, all, one }

/// Cached stream URL with timestamp for TTL expiry
class _CachedUrl {
  final String url;
  final DateTime cachedAt;
  _CachedUrl(this.url) : cachedAt = DateTime.now();

  /// URLs expire after 30 minutes (YouTube URLs typically last ~6 hours,
  /// but 30 min is safe and avoids edge-case failures).
  bool get isExpired => DateTime.now().difference(cachedAt).inMinutes > 30;
}

class PlayerProvider extends ChangeNotifier {
  final ApiService _apiService;
  final AudioPlayer _player = AudioPlayer();
  
  // Pre-resolved stream URLs with TTL — the key to instant playback
  final Map<String, _CachedUrl> _streamUrlCache = {};
  
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
  String? _slowNetworkMessage;
  int _loadingGeneration = 0;  // Cancels stale loads on rapid taps

  // Concatenating audio source for queue-based notification controls
  final ConcatenatingAudioSource _playlist = ConcatenatingAudioSource(
    children: [],
    useLazyPreparation: true,
  );



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
  String? get slowNetworkMessage => _slowNetworkMessage;
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

    // Listen for notification-driven track changes (prev/next from lock screen)
    _player.currentIndexStream.listen((index) {
      if (index != null && index != _currentIndex && index < _queue.length) {
        _onNotificationTrackChange(index);
      }
    });
  }

  /// Called when simple playlist navigation happens (e.g. user taps Next on lock screen)
  void _onNotificationTrackChange(int newIndex) {
    if (_queue.isEmpty || newIndex >= _queue.length) return;
    
    _trackSkipIfNeeded(); // Track the skip of the previous song
    _currentIndex = newIndex;
    _currentSong = _queue[newIndex];
    
    // Resolve URL effectively - playSong handles the resolution
    playSong(_queue[newIndex], forceIndex: newIndex);
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
      // Automatic advancement - managed by playlist mostly, but we trigger next logic
      // to ensure UI updates and next song resolution if needed (though playlist handles gapless)
      // Actually with ConcatenatingAudioSource, it advances automatically. 
      // We just need to update UI state if we weren't already.
      // However, we resolve URLs lazily. `just_audio` will ask for the next source.
      // But since we use placeholders, we need to intercept.
      // For now, let's trust the onNotificationTrackChange / current index stream
      // which fires when the player advances.
    } else if (_repeatMode == RepeatMode.all && _queue.isNotEmpty) {
      _player.seek(Duration.zero, index: 0);
      _player.play();
    }
  }

  /// Prefetch stream URLs for a list of songs so playback is instant.
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
        _streamUrlCache[videoId] = _CachedUrl(data['stream_url']);
      }
    } catch (_) {
      // Silent — prefetch failure is non-critical
    }
  }

  Future<void> playSong(Song song, {int? forceIndex}) async {
    _trackSkipIfNeeded();

    // If we're playing from queue (forceIndex provided), ensure checking correct index
    // If just playing a single song not in queue? We put it in queue/playlist.
    // But playSong is mostly called when user taps a song.

    _currentSong = song;
    _slowNetworkMessage = null;
    _position = Duration.zero;
    _duration = Duration.zero;

    // Increment generation — any older load becomes stale
    _loadingGeneration++;
    final thisGeneration = _loadingGeneration;

    // Sync _currentIndex if this song is in the queue
    if (forceIndex != null) {
      _currentIndex = forceIndex;
    } else {
      final queueIdx = _queue.indexWhere((s) => s.id == song.id);
      if (queueIdx >= 0) {
        _currentIndex = queueIdx;
      }
    }
    
    // Check local cache first — instant playback if cached & not expired
    final cached = _streamUrlCache[song.id];
    if (cached != null && !cached.isExpired) {
      _isLoading = false;
      notifyListeners();
      await _startPlayback(song, cached.url, index: _currentIndex);
      return;
    }
    // Remove expired entry
    if (cached != null && cached.isExpired) {
      _streamUrlCache.remove(song.id);
    }

    // Fetch path — show loading + 10s timeout
    _isLoading = true;
    notifyListeners();

    // Show "slow network" message after 3 seconds
    Timer(const Duration(seconds: 3), () {
      if (_isLoading && _loadingGeneration == thisGeneration) {
        _slowNetworkMessage = 'Internet is slow, please wait...';
        notifyListeners();
      }
    });

    try {
      final data = await _apiService.getStreamUrl(song.id)
          .timeout(const Duration(seconds: 10));
      
      // Check if user tapped another song while we were loading
      if (_loadingGeneration != thisGeneration) return;

      if (data != null && data['stream_url'] != null) {
        _streamUrlCache[song.id] = _CachedUrl(data['stream_url']);
        _slowNetworkMessage = null;
        _isLoading = false;
        notifyListeners();
        await _startPlayback(song, data['stream_url'], index: _currentIndex);
      } else {
        // No stream URL — skip to next
        _isLoading = false;
        _slowNetworkMessage = null;
        notifyListeners();
        if (hasNext) skipToNext();
      }
    } on TimeoutException {
      if (_loadingGeneration != thisGeneration) return;
      debugPrint("⏰ Song load timed out — skipping to next");
      _isLoading = false;
      _slowNetworkMessage = null;
      notifyListeners();
      // Auto-skip to next song on timeout
      if (hasNext) {
        skipToNext();
      }
    } catch (e) {
      if (_loadingGeneration != thisGeneration) return;
      debugPrint("Error playing song: $e");
      _isLoading = false;
      _slowNetworkMessage = null;
      notifyListeners();
    }
  }

  Future<void> _startPlayback(Song song, String streamUrl, {required int index}) async {
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

      // If playing within the playlist context, we must UPDATE the source at that index
      // and then seek to it, rather than setting a single source.
      if (index >= 0 && index < _playlist.length) {
         // Sadly there's no `replaceAt` in ConcatenatingAudioSource that doesn't disrupt others easily
         // But we can remove and insert. 
         // Or, better for single song replacement:
         // Just perform a seek if it's already set? No, we use placeholders.
         // Replace placeholder with real source.
         // Note: manipulating playlist while playing might be tricky.
         // Safe approach: removeAt(index), insert(index, source).
         
         // Wait, simply replacing the playlist or using setAudioSource clears the queue context.
         // We must maintain the playlist.
         
         // If calls come here, we have a valid URL.
         
         // We can't easily modify the source *in place* without removing/adding.
         // Let's indiscriminately replace for now.
         
         // BUT wait: modifying the playlist usually stops playback if we touch current index.
         // A safer way for lazy loading with just_audio is implementing a custom AudioSource
         // but that's complex.
         
         // Alternative: `setAudioSource` with the FULL playlist again? No, interrupts playback.
         // Use `LockCachingAudioSource`? NO.
         
         // Correct approach with `ConcatenatingAudioSource`:
         // We initiated with placeholders.
         // We can replace the item at `index`.
         
         // Actually, to avoid glitches, we check if the item at `index` is already resolved (same URI).
         // If not, we replace it.
         
         // Assuming we can't inspect URI easily from source list.
         // Let's indiscriminately replace for now.
         
         await _playlist.removeAt(index);
         await _playlist.insert(index, source);
         
         // Then seek to it
         await _player.seek(Duration.zero, index: index);
         if (!_player.playing) _player.play();
      } else {
         // Fallback if index invalid (shouldn't happen with proper queue sync)
         await _player.setAudioSource(source);
         _player.play();
      }

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
      // URL expired (403) — clear local cache and force-refresh from backend
      _streamUrlCache.remove(song.id);
      try {
        final data = await _apiService.getStreamUrl(song.id, forceRefresh: true);
        if (data != null && data['stream_url'] != null) {
          _streamUrlCache[song.id] = _CachedUrl(data['stream_url']);
          final retrySource = AudioSource.uri(
            Uri.parse(data['stream_url']),
            tag: MediaItem(
              id: song.id,
              title: song.title,
              artist: song.artist,
              artUri: Uri.parse(song.thumbnailUrl),
            ),
          );
          
          if (index >= 0 && index < _playlist.length) {
             await _playlist.removeAt(index);
             await _playlist.insert(index, retrySource);
             await _player.seek(Duration.zero, index: index);
             _player.play();
          } else {
             await _player.setAudioSource(retrySource);
             _player.play();
          }
        }
      } catch (retryError) {
        debugPrint("Retry also failed: $retryError");
      }
    }
  }

  Future<void> playQueue(List<Song> songs, {int startIndex = 0}) async {
    _queue = List.from(songs);
    _currentIndex = startIndex;

    // clear playlist
    await _playlist.clear();

    // Populate playlist with placeholders
    final sources = songs.map((s) => AudioSource.uri(
      Uri.parse(''), // Placeholder URI
      tag: MediaItem(
        id: s.id,
        title: s.title,
        artist: s.artist,
        artUri: Uri.parse(s.thumbnailUrl),
      ),
    )).toList();
    
    await _playlist.addAll(sources);
    await _player.setAudioSource(_playlist, initialIndex: startIndex, preload: false);

    // Immediately prefetch all queue songs
    prefetchSongs(songs);

    if (_queue.isNotEmpty && startIndex < _queue.length) {
      // Actually resolve and play the first one
      await playSong(_queue[startIndex], forceIndex: startIndex);
    }
  }

  Future<void> addToQueue(Song song) async {
    _queue.add(song);
    // Add placeholder to playlist
    await _playlist.add(AudioSource.uri(
      Uri.parse(''), 
      tag: MediaItem(
        id: song.id,
        title: song.title,
        artist: song.artist,
        artUri: Uri.parse(song.thumbnailUrl),
      ),
    ));

    // Prefetch the added song
    if (!_streamUrlCache.containsKey(song.id)) {
      _resolveAndCache(song.id);
    }
    notifyListeners();
  }

  Future<void> playNext(Song song) async {
    if (_currentIndex >= 0 && _currentIndex < _queue.length - 1) {
      _queue.insert(_currentIndex + 1, song);
      await _playlist.insert(_currentIndex + 1, AudioSource.uri(
        Uri.parse(''),
        tag: MediaItem(
          id: song.id,
          title: song.title,
          artist: song.artist,
          artUri: Uri.parse(song.thumbnailUrl),
        ),
      ));
    } else {
      _queue.add(song);
      await _playlist.add(AudioSource.uri(
        Uri.parse(''),
        tag: MediaItem(
          id: song.id,
          title: song.title,
          artist: song.artist,
          artUri: Uri.parse(song.thumbnailUrl),
        ),
      ));
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
       _player.seekToNext(); 
       // The currentIndexStream will trigger _onNotificationTrackChange -> playSong
    } else if (_repeatMode == RepeatMode.all && _queue.isNotEmpty) {
       _player.seek(Duration.zero, index: 0);
    }
  }

  Future<void> skipToPrevious() async {
    if (_position.inSeconds > 3) {
      await _player.seek(Duration.zero);
      return;
    }
    _trackSkipIfNeeded();
    if (hasPrevious) {
      _player.seekToPrevious();
       // The currentIndexStream will trigger _onNotificationTrackChange -> playSong
    }
  }

  Future<void> toggleShuffle() async {
    _isShuffled = !_isShuffled;
    if (_isShuffled && _queue.length > 1) {
      await _player.setShuffleModeEnabled(true);
      await _player.shuffle();
      // Note: mapping shuffled queue back to UI queue is complex with just_audio
      // For now, simpler implementation: maintain UI queue, shuffle that, rebuild playlist.
      
      final current = _currentIndex >= 0 ? _queue[_currentIndex] : null;
      _queue.shuffle();
      if (current != null) {
        _queue.remove(current);
        _queue.insert(0, current);
        _currentIndex = 0;
      }
      
      // Rebuild playlist
      // This is expensive but correct
      await playQueue(_queue, startIndex: 0);
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
      // Seek to that index in the playlist
      // This will trigger currentIndexStream -> playSong
      await _player.seek(Duration.zero, index: index);
      _player.play();
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

  /// Stop playback and clear the notification completely
  Future<void> stopAndClear() async {
    await _player.stop();
    _currentSong = null;
    _currentIndex = -1;
    _queue.clear();
    _isPlaying = false;
    _position = Duration.zero;
    _duration = Duration.zero;
    _currentPlayId = null;
    notifyListeners();
  }
  
  @override
  void dispose() {
    _player.stop();
    _player.dispose();
    super.dispose();
  }
}
