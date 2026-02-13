
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class LibraryProvider extends ChangeNotifier {
  final ApiService _apiService;

  List<Playlist> _playlists = [];
  List<AutoPlaylist> _autoPlaylists = [];
  List<PlayHistoryItem> _playHistory = [];
  Set<String> _likedSongIds = {};
  bool _isLoading = false;
  String? _error;

  LibraryProvider(this._apiService);

  List<Playlist> get playlists => _playlists;
  List<AutoPlaylist> get autoPlaylists => _autoPlaylists;
  List<PlayHistoryItem> get playHistory => _playHistory;
  bool get isLoading => _isLoading;
  String? get error => _error;

  bool isSongLiked(String songId) => _likedSongIds.contains(songId);

  Future<void> fetchAll() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      await Future.wait([
        fetchPlaylists(),
        fetchPlayHistory(),
        fetchAutoPlaylists(),
      ]);
    } catch (e) {
      _error = 'Failed to load library';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchPlaylists() async {
    try {
      _playlists = await _apiService.getMyPlaylists();
      notifyListeners();
    } catch (_) {}
  }

  Future<void> fetchAutoPlaylists() async {
    try {
      _autoPlaylists = await _apiService.getAutoPlaylists();
      notifyListeners();
    } catch (_) {}
  }

  Future<void> fetchPlayHistory() async {
    try {
      _playHistory = await _apiService.getPlayHistory(limit: 50);
      notifyListeners();
    } catch (_) {}
  }

  Future<bool> toggleLike(Song song) async {
    try {
      final response = await _apiService.likeSong(song);
      final liked = response['liked'] ?? false;
      if (liked) {
        _likedSongIds.add(song.id);
      } else {
        _likedSongIds.remove(song.id);
      }
      notifyListeners();
      return liked;
    } catch (_) {
      return false;
    }
  }

  Future<bool> createPlaylist(String name) async {
    try {
      await _apiService.createPlaylist(name);
      await fetchPlaylists();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<bool> addSongToPlaylist(String playlistId, String songId) async {
    try {
      await _apiService.addSongToPlaylist(playlistId, songId);
      await fetchPlaylists();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<AutoPlaylist?> generateAutoPlaylist({String algorithm = 'smart'}) async {
    try {
      final playlist = await _apiService.generateAutoPlaylist(algorithm: algorithm);
      await fetchAutoPlaylists();
      return playlist;
    } catch (_) {
      return null;
    }
  }

  Future<void> clearHistory() async {
    try {
      await _apiService.clearHistory();
      _playHistory = [];
      notifyListeners();
    } catch (_) {}
  }
}
