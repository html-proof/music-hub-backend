
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../providers/search_provider.dart';
import '../../providers/player_provider.dart';
import '../../widgets/song_tile.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  static const moodChips = [
    ('😊 Happy', 'happy songs'), ('😢 Sad', 'sad songs'),
    ('💕 Romantic', 'romantic songs'), ('⚡ Energetic', 'energetic songs'),
    ('🎉 Party', 'party songs'), ('😎 Chill', 'chill songs'),
    ('💪 Workout', 'workout songs'), ('🎯 Focus', 'focus music'),
  ];

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final search = Provider.of<SearchProvider>(context);
    final player = Provider.of<PlayerProvider>(context, listen: false);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Search Bar
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  decoration: InputDecoration(
                    hintText: 'Search songs, artists...',
                    hintStyle: TextStyle(color: Colors.grey[500]),
                    prefixIcon: Icon(Icons.search_rounded, color: Colors.grey[400]),
                    suffixIcon: _controller.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.close, color: Colors.white54),
                            onPressed: () {
                              _controller.clear();
                              search.clear();
                            },
                          )
                        : null,
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                  ),
                  style: const TextStyle(color: Colors.white, fontSize: 16),
                  textInputAction: TextInputAction.search,
                  onChanged: (v) {
                    search.onQueryChanged(v);
                    setState(() {});
                  },
                  onSubmitted: (v) => search.search(v),
                ),
              ),
            ),

            // Content
            Expanded(
              child: search.isLoading
                  ? const Center(
                      child: CircularProgressIndicator(color: Color(0xFF7C3AED)),
                    )
                  : search.error != null
                      ? Center(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.error_outline, size: 48, color: Colors.white24),
                              const SizedBox(height: 12),
                              Text(search.error!, style: TextStyle(color: Colors.grey[400])),
                            ],
                          ),
                        )
                      : search.results.isNotEmpty
                          ? _buildResults(search, player)
                          : search.suggestions.isNotEmpty
                              ? _buildSuggestions(search)
                              : _buildBrowse(search),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResults(SearchProvider search, PlayerProvider player) {
    // Pre-resolve stream URLs so play is instant
    player.prefetchSongs(search.results);
    
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 120),
      itemCount: search.results.length,
      itemBuilder: (context, index) {
        final song = search.results[index];
        return SongTile(
          song: song,
          onTap: () => player.playQueue(search.results, startIndex: index),
        ).animate().fadeIn(delay: (index * 30).ms);
      },
    );
  }

  Widget _buildSuggestions(SearchProvider search) {
    return ListView.builder(
      padding: const EdgeInsets.only(top: 8),
      itemCount: search.suggestions.length,
      itemBuilder: (context, index) {
        final suggestion = search.suggestions[index];
        return ListTile(
          leading: const Icon(Icons.trending_up, color: Colors.white38),
          title: Text(suggestion, style: const TextStyle(color: Colors.white70)),
          onTap: () {
            _controller.text = suggestion;
            search.search(suggestion);
          },
        );
      },
    );
  }

  Widget _buildBrowse(SearchProvider search) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 24),
          const Text(
            'Browse by Mood',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: moodChips.map((chip) {
              return InkWell(
                onTap: () {
                  _controller.text = chip.$2;
                  search.search(chip.$2);
                },
                borderRadius: BorderRadius.circular(24),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        const Color(0xFF7C3AED).withOpacity(0.2),
                        const Color(0xFFEC4899).withOpacity(0.1),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: Colors.white10),
                  ),
                  child: Text(
                    chip.$1,
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 80),
          Center(
            child: Column(
              children: [
                Icon(Icons.search_rounded, size: 64, color: Colors.grey[800]),
                const SizedBox(height: 12),
                Text(
                  'Search for your favorite music',
                  style: TextStyle(color: Colors.grey[600], fontSize: 15),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
