
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../providers/library_provider.dart';
import '../../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  String _selectedLanguage = 'english';
  final Set<String> _selectedMoods = {};
  bool _isSaving = false;
  bool _isLoadingPrefs = true;

  static const languages = [
    'english', 'hindi', 'tamil', 'telugu', 'punjabi',
    'malayalam', 'kannada', 'bengali', 'marathi', 'korean', 'spanish',
  ];

  static const moods = [
    'happy', 'sad', 'romantic', 'energetic', 'calm', 'party',
    'workout', 'focus', 'chill', 'motivational', 'nostalgic', 'devotional',
  ];

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final prefs = await api.getPreferences();
      if (mounted) {
        setState(() {
          _selectedLanguage = prefs['language'] ?? 'english';
          _selectedMoods.addAll((prefs['moods'] as List?)?.cast<String>() ?? []);
          _isLoadingPrefs = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoadingPrefs = false);
    }
  }

  Future<void> _savePreferences() async {
    setState(() => _isSaving = true);
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      await api.savePreferences(
        language: _selectedLanguage,
        moods: _selectedMoods.toList(),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Preferences updated'),
            backgroundColor: Color(0xFF7C3AED),
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to save preferences')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: _isLoadingPrefs
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF7C3AED)))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Language
                _sectionTitle('Language'),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: languages.map((lang) {
                    final selected = _selectedLanguage == lang;
                    return ChoiceChip(
                      label: Text(lang[0].toUpperCase() + lang.substring(1)),
                      selected: selected,
                      selectedColor: const Color(0xFF7C3AED),
                      backgroundColor: const Color(0xFF1E1E2E),
                      labelStyle: TextStyle(
                        color: selected ? Colors.white : Colors.white70,
                      ),
                      onSelected: (v) {
                        if (v) setState(() => _selectedLanguage = lang);
                      },
                    );
                  }).toList(),
                ),

                const SizedBox(height: 24),

                // Moods
                _sectionTitle('Preferred Moods'),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: moods.map((mood) {
                    final selected = _selectedMoods.contains(mood);
                    return FilterChip(
                      label: Text(mood[0].toUpperCase() + mood.substring(1)),
                      selected: selected,
                      selectedColor: const Color(0xFF7C3AED),
                      backgroundColor: const Color(0xFF1E1E2E),
                      checkmarkColor: Colors.white,
                      labelStyle: TextStyle(
                        color: selected ? Colors.white : Colors.white70,
                      ),
                      onSelected: (v) {
                        setState(() {
                          if (v && _selectedMoods.length < 3) {
                            _selectedMoods.add(mood);
                          } else {
                            _selectedMoods.remove(mood);
                          }
                        });
                      },
                    );
                  }).toList(),
                ),

                const SizedBox(height: 24),

                // Save preferences
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isSaving ? null : _savePreferences,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF7C3AED),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: _isSaving
                        ? const SizedBox(
                            width: 20, height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Save Preferences', style: TextStyle(fontWeight: FontWeight.w600)),
                  ),
                ),

                const SizedBox(height: 32),
                const Divider(color: Colors.white12),
                const SizedBox(height: 16),

                // Clear History
                ListTile(
                  leading: const Icon(Icons.delete_outline, color: Colors.orange),
                  title: const Text('Clear History', style: TextStyle(color: Colors.white)),
                  subtitle: Text('Remove all play and search history',
                      style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                  onTap: () => _showClearDialog(context),
                ),

                const SizedBox(height: 8),

                // Logout
                ListTile(
                  leading: const Icon(Icons.logout, color: Colors.redAccent),
                  title: const Text('Logout', style: TextStyle(color: Colors.redAccent)),
                  onTap: () => _showLogoutDialog(context),
                ),

                const SizedBox(height: 80),
              ],
            ),
    );
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title,
        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
      ),
    );
  }

  void _showClearDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E2E),
        title: const Text('Clear History?', style: TextStyle(color: Colors.white)),
        content: const Text(
          'This will remove all your play and search history. Your preferences will be kept.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
          ),
          TextButton(
            onPressed: () {
              Provider.of<LibraryProvider>(ctx, listen: false).clearHistory();
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('History cleared'), backgroundColor: Color(0xFF7C3AED)),
              );
            },
            child: const Text('Clear', style: TextStyle(color: Colors.orange)),
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E2E),
        title: const Text('Logout?', style: TextStyle(color: Colors.white)),
        content: const Text(
          'You will need to sign in again to use the app.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
          ),
          TextButton(
            onPressed: () {
              Provider.of<AuthProvider>(ctx, listen: false).logout();
              Navigator.pop(ctx);
            },
            child: const Text('Logout', style: TextStyle(color: Colors.redAccent)),
          ),
        ],
      ),
    );
  }
}
