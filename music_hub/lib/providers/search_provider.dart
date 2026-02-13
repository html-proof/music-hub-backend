
import 'dart:async';
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class SearchProvider extends ChangeNotifier {
  final ApiService _apiService;
  
  List<Song> _results = [];
  List<String> _suggestions = [];
  bool _isLoading = false;
  bool _isSuggestionsLoading = false;
  String? _error;
  String _currentQuery = '';
  Timer? _debounce;

  SearchProvider(this._apiService);

  List<Song> get results => _results;
  List<String> get suggestions => _suggestions;
  bool get isLoading => _isLoading;
  bool get isSuggestionsLoading => _isSuggestionsLoading;
  String? get error => _error;
  String get currentQuery => _currentQuery;

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
