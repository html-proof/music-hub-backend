
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class HomeProvider extends ChangeNotifier {
  final ApiService _apiService;
  
  List<RecommendationSection> _sections = [];
  bool _isLoading = false;
  String? _error;

  HomeProvider(this._apiService);

  List<RecommendationSection> get sections => _sections;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchHomeData({String? uid}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // Primary: RTDB-powered feed based on user's language & moods
      final rtdbSections = await _apiService.getLanguageMoodFeed();

      if (rtdbSections.isNotEmpty) {
        _sections = rtdbSections.where((s) => s.songs.isNotEmpty).toList();
      } else {
        // Fallback: generic recommendations if user not onboarded yet
        final results = await Future.wait([
          _fetchSection('🎵 Trending', '🎵', () => _apiService.getPersonalized()),
          _fetchSection('🔥 For You', '🔥', () => uid != null
              ? _apiService.getForYou(uid)
              : _apiService.getPersonalized()),
          _fetchSection('💿 Daily Mix', '💿', () => uid != null
              ? _apiService.getDailyMix(uid)
              : _apiService.getSmartFeed()),
          _fetchSection('✨ Smart Picks', '✨', () => _apiService.getSmartFeed()),
        ]);
        _sections = results.where((s) => s.songs.isNotEmpty).toList();
      }

      if (_sections.isEmpty) {
        _error = 'No recommendations yet. Search and play some music first!';
      }
    } catch (e) {
      _error = 'Failed to load recommendations';
      debugPrint('HomeProvider error: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<RecommendationSection> _fetchSection(
    String title,
    String icon,
    Future<List<Song>> Function() fetcher,
  ) async {
    try {
      final songs = await fetcher();
      return RecommendationSection(title: title, icon: icon, songs: songs);
    } catch (_) {
      return RecommendationSection(title: title, icon: icon, songs: []);
    }
  }

  Future<void> refresh({String? uid}) async {
    await fetchHomeData(uid: uid);
  }
}
