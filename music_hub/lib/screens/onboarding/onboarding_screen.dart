
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../services/api_service.dart';
import '../../providers/auth_provider.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  int _step = 0; // 0 = language, 1 = moods
  String? _selectedLanguage;
  final Set<String> _selectedMoods = {};
  bool _isSubmitting = false;

  static const languages = [
    'english', 'hindi', 'tamil', 'telugu', 'punjabi',
    'malayalam', 'kannada', 'bengali', 'marathi', 'korean', 'spanish',
  ];

  static const moods = [
    ('happy', '😊'), ('sad', '😢'), ('romantic', '💕'),
    ('energetic', '⚡'), ('calm', '🌊'), ('party', '🎉'),
    ('workout', '💪'), ('focus', '🎯'), ('chill', '😎'),
    ('motivational', '🚀'), ('nostalgic', '✨'), ('devotional', '🙏'),
  ];

  static const languageEmojis = {
    'english': '🇺🇸', 'hindi': '🇮🇳', 'tamil': '🎶', 'telugu': '🎵',
    'punjabi': '🎤', 'malayalam': '🌴', 'kannada': '🏛️', 'bengali': '🎭',
    'marathi': '🎪', 'korean': '🇰🇷', 'spanish': '🇪🇸',
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF0A0A1A), Color(0xFF1A0A2E), Color(0xFF0A0A1A)],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Progress indicator
                Row(
                  children: [
                    Expanded(
                      child: Container(
                        height: 4,
                        decoration: BoxDecoration(
                          color: const Color(0xFF7C3AED),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Container(
                        height: 4,
                        decoration: BoxDecoration(
                          color: _step >= 1 ? const Color(0xFF7C3AED) : Colors.white12,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 40),

                // Title
                Text(
                  _step == 0 ? 'Choose Your\nLanguage' : 'Pick Your\nMoods',
                  style: GoogleFonts.outfit(
                    fontSize: 36,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                    height: 1.2,
                  ),
                ).animate().fadeIn(duration: 300.ms).slideX(begin: 0.1),
                const SizedBox(height: 8),
                Text(
                  _step == 0
                      ? 'What language do you prefer for music?'
                      : 'Select 1-3 moods that match your vibe',
                  style: TextStyle(color: Colors.grey[400], fontSize: 16),
                ).animate().fadeIn(delay: 100.ms),
                const SizedBox(height: 32),

                // Content
                Expanded(
                  child: _step == 0 ? _buildLanguageGrid() : _buildMoodGrid(),
                ),

                // Bottom button
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: ElevatedButton(
                    onPressed: _canProceed() ? _onNext : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF7C3AED),
                      disabledBackgroundColor: Colors.white10,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    child: _isSubmitting
                        ? const SizedBox(
                            width: 24, height: 24,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : Text(
                            _step == 0 ? 'Continue' : 'Get Started 🎵',
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                          ),
                  ),
                ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.2),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLanguageGrid() {
    return GridView.builder(
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        childAspectRatio: 2.5,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: languages.length,
      itemBuilder: (context, index) {
        final lang = languages[index];
        final selected = _selectedLanguage == lang;
        return InkWell(
          onTap: () => setState(() => _selectedLanguage = lang),
          borderRadius: BorderRadius.circular(14),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              color: selected ? const Color(0xFF7C3AED).withOpacity(0.2) : Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: selected ? const Color(0xFF7C3AED) : Colors.white10,
                width: selected ? 2 : 1,
              ),
            ),
            child: Center(
              child: Text(
                '${languageEmojis[lang] ?? '🎵'} ${lang[0].toUpperCase()}${lang.substring(1)}',
                style: TextStyle(
                  color: selected ? Colors.white : Colors.white70,
                  fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                  fontSize: 15,
                ),
              ),
            ),
          ),
        ).animate().fadeIn(delay: (index * 50).ms).scale(begin: const Offset(0.95, 0.95));
      },
    );
  }

  Widget _buildMoodGrid() {
    return GridView.builder(
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        childAspectRatio: 1.1,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
      ),
      itemCount: moods.length,
      itemBuilder: (context, index) {
        final (mood, emoji) = moods[index];
        final selected = _selectedMoods.contains(mood);
        return InkWell(
          onTap: () {
            setState(() {
              if (selected) {
                _selectedMoods.remove(mood);
              } else if (_selectedMoods.length < 3) {
                _selectedMoods.add(mood);
              }
            });
          },
          borderRadius: BorderRadius.circular(16),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              gradient: selected
                  ? const LinearGradient(
                      colors: [Color(0xFF7C3AED), Color(0xFFEC4899)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    )
                  : null,
              color: selected ? null : Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: selected ? Colors.transparent : Colors.white10,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(emoji, style: const TextStyle(fontSize: 28)),
                const SizedBox(height: 6),
                Text(
                  mood[0].toUpperCase() + mood.substring(1),
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ).animate().fadeIn(delay: (index * 40).ms).scale(begin: const Offset(0.9, 0.9));
      },
    );
  }

  bool _canProceed() {
    if (_isSubmitting) return false;
    if (_step == 0) return _selectedLanguage != null;
    return _selectedMoods.isNotEmpty && _selectedMoods.length <= 3;
  }

  Future<void> _onNext() async {
    if (_step == 0) {
      setState(() => _step = 1);
      return;
    }

    // Submit onboarding
    setState(() => _isSubmitting = true);

    try {
      final api = Provider.of<ApiService>(context, listen: false);
      await api.saveOnboarding(
        language: _selectedLanguage!,
        moods: _selectedMoods.toList(),
      );
      if (mounted) {
        Provider.of<AuthProvider>(context, listen: false).completeOnboarding();
      }
    } catch (e) {
      // Even if backend fails, allow user through
      if (mounted) {
        Provider.of<AuthProvider>(context, listen: false).completeOnboarding();
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }
}
