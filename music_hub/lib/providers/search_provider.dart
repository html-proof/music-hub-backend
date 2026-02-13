import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class SearchProvider extends ChangeNotifier {
  final ApiService _apiService;
  
  List<Song> _results = [];
  List<String> _suggestions = [];
  List<String> _searchHistory = [];
  bool _isLoading = false;
  bool _isSuggestionsLoading = false;
  String? _error;
  String _currentQuery = '';
  Timer? _debounce;
  static const String _historyKey = 'search_history';

  SearchProvider(this._apiService) {
    _loadHistory();
  }

  List<Song> get results => _results;
  List<String> get suggestions => _suggestions;
  List<String> get searchHistory => _searchHistory;
  bool get isLoading => _isLoading;
  bool get isSuggestionsLoading => _isSuggestionsLoading;
  String? get error => _error;
  String get currentQuery => _currentQuery;

  Future<void> _loadHistory() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _searchHistory = prefs.getStringList(_historyKey) ?? [];
      notifyListeners();
    } catch (e) {
      debugPrint('Error loading search history: $e');
    }
  }

  Future<void> _saveHistory() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setStringList(_historyKey, _searchHistory);
    } catch (e) {
      debugPrint('Error saving search history: $e');
    }
  }

  void onQueryChanged(String query) {
    _currentQuery = query;
    _debounce?.cancel();
    
    if (query.length < 2) {
      _suggestions = [];
      notifyListeners();
      return;
    }

    _debounce = Timer(const Duration(milliseconds: 300), () {
      _fetchSuggestions(query);
    });
  }

  Future<void> _fetchSuggestions(String query) async {
    _isSuggestionsLoading = true;
    notifyListeners();

    try {
      _suggestions = await _apiService.getSearchSuggestions(query);
    } catch (_) {
      _suggestions = [];
    } finally {
      _isSuggestionsLoading = false;
      notifyListeners();
    }
  }

  Future<void> search(String query) async {
    if (query.trim().isEmpty) return;
    
    _currentQuery = query;
    _isLoading = true;
    _error = null;
    _suggestions = [];
    notifyListeners();

    // Add to search history
    _addToHistory(query.trim());

    try {
      _results = await _apiService.searchSongs(query);
      
      // Track search in background
      _apiService.trackSearch(query, _results.length);
    } catch (e) {
      _error = 'Search failed. Please try again.';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void _addToHistory(String query) {
    // Remove if already exists (move to top)
    _searchHistory.remove(query);
    _searchHistory.insert(0, query);
    // Keep max 15
    if (_searchHistory.length > 15) {
      _searchHistory = _searchHistory.sublist(0, 15);
    }
    _saveHistory();
  }

  void removeFromHistory(String query) {
    _searchHistory.remove(query);
    _saveHistory();
    notifyListeners();
  }

  void clearHistory() {
    _searchHistory.clear();
    _saveHistory();
    notifyListeners();
  }

  void clear() {
    _results = [];
    _suggestions = [];
    _currentQuery = '';
    _error = null;
    notifyListeners();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }
}
