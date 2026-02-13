
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/constants.dart';
import '../models/models.dart';

class ApiService {
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.apiBaseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: AppConstants.tokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (DioException e, handler) {
        return handler.next(e);
      },
    ));
  }

  Dio get client => _dio;

  // ==================== AUTH ====================

  Future<Map<String, dynamic>> login(String firebaseToken) async {
    final response = await _dio.post('/auth/login', data: {
      'firebase_token': firebaseToken,
    });
    return response.data;
  }

  Future<void> logout() async {
    try {
      await _dio.post('/auth/logout');
    } catch (_) {}
  }

  Future<Map<String, dynamic>> getMe() async {
    final response = await _dio.get('/auth/me');
    return response.data;
  }

  // ==================== MUSIC ====================

  Future<List<Song>> searchSongs(String query) async {
    final response = await _dio.get('/music/search', queryParameters: {'q': query});
    if (response.statusCode == 200 && response.data['results'] != null) {
      return (response.data['results'] as List)
          .map((e) => Song.fromJson(e))
          .toList();
    }
    return [];
  }

  Future<Map<String, dynamic>?> getStreamUrl(String videoId, {String quality = 'high'}) async {
    final response = await _dio.get('/music/play', queryParameters: {
      'id': videoId,
      'quality': quality,
    });
    if (response.statusCode == 200 && response.data['success'] == true) {
      return response.data['data'];
    }
    return null;
  }

  Future<void> prefetchSongs(List<String> ids, {String quality = 'high'}) async {
    try {
      await _dio.post('/music/prefetch', data: {
        'ids': ids,
        'quality': quality,
      });
    } catch (_) {}
  }

  // ==================== RECOMMENDATIONS ====================

  Future<List<Song>> getPersonalized() async {
    final response = await _dio.get('/recommend/personalized');
    if (response.statusCode == 200 && response.data['success'] == true) {
      return (response.data['data'] as List).map((e) => Song.fromJson(e)).toList();
    }
    return [];
  }

  Future<List<Song>> getForYou(String uid) async {
    final response = await _dio.get('/recommend/for-you', queryParameters: {'uid': uid});
    if (response.statusCode == 200 && response.data['success'] == true) {
      return (response.data['data'] as List).map((e) => Song.fromJson(e)).toList();
    }
    return [];
  }

  Future<List<Song>> getDailyMix(String uid) async {
    final response = await _dio.get('/recommend/daily-mix', queryParameters: {'uid': uid});
    if (response.statusCode == 200 && response.data['success'] == true) {
      return (response.data['data'] as List).map((e) => Song.fromJson(e)).toList();
    }
    return [];
  }

  Future<List<Song>> getMoodRecs(String uid, String mood) async {
    final response = await _dio.get('/recommend/mood', queryParameters: {'uid': uid, 'mood': mood});
    if (response.statusCode == 200 && response.data['success'] == true) {
      return (response.data['data'] as List).map((e) => Song.fromJson(e)).toList();
    }
    return [];
  }

  Future<List<Song>> getSimilar(String videoId) async {
    final response = await _dio.get('/recommend/similar', queryParameters: {'id': videoId});
    if (response.statusCode == 200 && response.data['success'] == true) {
      return (response.data['data'] as List).map((e) => Song.fromJson(e)).toList();
    }
    return [];
  }

  Future<List<Song>> getSmartFeed({int page = 1, int pageSize = 20}) async {
    final response = await _dio.get('/recommend/smart/feed', queryParameters: {
      'page': page,
      'page_size': pageSize,
    });
    if (response.statusCode == 200 && response.data['success'] == true) {
      return (response.data['songs'] as List).map((e) => Song.fromJson(e)).toList();
    }
    return [];
  }

  /// Fetch personalized home feed based on user's language & moods from RTDB.
  /// Returns sections with titles and song lists.
  Future<List<RecommendationSection>> getLanguageMoodFeed() async {
    final response = await _dio.get('/recommend/home-feed');
    if (response.statusCode == 200 && response.data['success'] == true) {
      final rawSections = response.data['sections'] as List? ?? [];
      return rawSections.map((s) {
        final title = s['title'] ?? 'Recommended';
        final songs = (s['songs'] as List? ?? [])
            .map((e) => Song.fromJson(e))
            .toList();
        return RecommendationSection(title: title, icon: '', songs: songs);
      }).toList();
    }
    return [];
  }

  // ==================== ONBOARDING ====================

  Future<Map<String, dynamic>> checkOnboarding() async {
    final response = await _dio.get('/user/check-onboarding');
    return response.data;
  }

  Future<Map<String, dynamic>> saveOnboarding({
    required String language,
    required List<String> moods,
    List<String> genres = const [],
  }) async {
    final response = await _dio.post('/user/onboarding', data: {
      'language': language,
      'moods': moods,
      'genres': genres,
    });
    return response.data;
  }

  // ==================== USER ====================

  Future<UserProfile> getProfile() async {
    final response = await _dio.get('/user/profile');
    return UserProfile.fromJson(response.data);
  }

  Future<Map<String, dynamic>> getPreferences() async {
    final response = await _dio.get('/user/preferences');
    return response.data;
  }

  Future<void> savePreferences({
    required String language,
    required List<String> moods,
    List<String> genres = const [],
  }) async {
    await _dio.post('/user/preferences', data: {
      'language': language,
      'moods': moods,
      'genres': genres,
    });
  }

  Future<UserInsights> getInsights() async {
    final response = await _dio.get('/user/insights');
    return UserInsights.fromJson(response.data);
  }

  Future<Map<String, dynamic>> getHomeFeed() async {
    final response = await _dio.get('/user/home-feed');
    return response.data;
  }

  // ==================== LIBRARY ====================

  Future<Map<String, dynamic>> likeSong(Song song) async {
    final response = await _dio.post('/library/like', data: {
      'song_id': song.id,
      'title': song.title,
      'artist': song.artist,
      'thumbnailUrl': song.thumbnailUrl,
      'audioUrl': song.audioUrl ?? '',
      'durationSeconds': song.durationSeconds,
    });
    return response.data;
  }

  // ==================== PLAYLISTS ====================

  Future<List<Playlist>> getMyPlaylists() async {
    final response = await _dio.get('/playlist/my');
    if (response.statusCode == 200 && response.data['playlists'] != null) {
      return (response.data['playlists'] as List)
          .map((e) => Playlist.fromJson(e))
          .toList();
    }
    return [];
  }

  Future<Map<String, dynamic>> createPlaylist(String name) async {
    final response = await _dio.post('/playlist/create', data: {'name': name});
    return response.data;
  }

  Future<void> addSongToPlaylist(String playlistId, String songId) async {
    await _dio.post('/playlist/$playlistId/add', data: {'song_id': songId});
  }

  // ==================== AUTO-PLAYLISTS ====================

  Future<AutoPlaylist> generateAutoPlaylist({String algorithm = 'smart'}) async {
    final response = await _dio.post('/auto-playlist/generate', queryParameters: {
      'algorithm': algorithm,
    });
    return AutoPlaylist.fromJson(response.data);
  }

  Future<List<AutoPlaylist>> getAutoPlaylists() async {
    final response = await _dio.get('/auto-playlist/list');
    if (response.statusCode == 200 && response.data['playlists'] != null) {
      return (response.data['playlists'] as List)
          .map((e) => AutoPlaylist.fromJson(e))
          .toList();
    }
    return [];
  }

  Future<AutoPlaylist> getAutoPlaylist(String playlistId) async {
    final response = await _dio.get('/auto-playlist/$playlistId');
    return AutoPlaylist.fromJson(response.data);
  }

  Future<void> deleteAutoPlaylist(String playlistId) async {
    await _dio.delete('/auto-playlist/$playlistId');
  }

  Future<void> clearHistory() async {
    await _dio.delete('/auto-playlist/history/clear');
  }

  // ==================== TRACKING ====================

  Future<String?> trackSearch(String query, int resultsCount, {String? clickedResult}) async {
    try {
      final response = await _dio.post('/track/search', data: {
        'search_query': query,
        'results_count': resultsCount,
        'clicked_result': clickedResult,
      });
      return response.data['search_id'];
    } catch (_) {
      return null;
    }
  }

  Future<String?> trackPlay({
    required String videoId,
    required String title,
    String artist = '',
    String channel = '',
    int duration = 0,
  }) async {
    try {
      final response = await _dio.post('/track/play', data: {
        'video_id': videoId,
        'title': title,
        'artist': artist,
        'channel': channel,
        'duration': duration,
      });
      return response.data['play_id'];
    } catch (_) {
      return null;
    }
  }

  Future<void> trackSkip(String playId, int playDuration) async {
    try {
      await _dio.post('/track/skip', data: {
        'play_id': playId,
        'play_duration': playDuration,
      });
    } catch (_) {}
  }

  Future<void> trackComplete(String playId, int playDuration) async {
    try {
      await _dio.post('/track/complete', data: {
        'play_id': playId,
        'play_duration': playDuration,
      });
    } catch (_) {}
  }

  Future<List<PlayHistoryItem>> getPlayHistory({int limit = 100}) async {
    final response = await _dio.get('/track/play-history', queryParameters: {'limit': limit});
    if (response.statusCode == 200 && response.data['plays'] != null) {
      return (response.data['plays'] as List)
          .map((e) => PlayHistoryItem.fromJson(e))
          .toList();
    }
    return [];
  }

  Future<List<String>> getSearchSuggestions(String query) async {
    try {
      final response = await _dio.get('/track/suggestions', queryParameters: {'q': query});
      if (response.statusCode == 200 && response.data['suggestions'] != null) {
        return (response.data['suggestions'] as List).cast<String>();
      }
    } catch (_) {}
    return [];
  }
}
