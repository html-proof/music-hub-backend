
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
                              : _buildHistory(search),
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

  Widget _buildHistory(SearchProvider search) {
    if (search.searchHistory.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_rounded, size: 64, color: Colors.grey[800]),
            const SizedBox(height: 12),
            Text(
              'Search for your favorite music',
              style: TextStyle(color: Colors.grey[600], fontSize: 15),
            ),
          ],
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Recent Searches',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              TextButton(
                onPressed: () => search.clearHistory(),
                child: const Text(
                  'Clear all',
                  style: TextStyle(color: Color(0xFF7C3AED), fontSize: 13),
                ),
              ),
            ],
          ),
        ),

        // History list
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.only(bottom: 120),
            itemCount: search.searchHistory.length,
            itemBuilder: (context, index) {
              final query = search.searchHistory[index];
              return Dismissible(
                key: Key(query),
                direction: DismissDirection.endToStart,
                onDismissed: (_) => search.removeFromHistory(query),
                background: Container(
                  alignment: Alignment.centerRight,
                  padding: const EdgeInsets.only(right: 20),
                  color: Colors.red.withOpacity(0.2),
                  child: const Icon(Icons.delete_outline, color: Colors.red),
                ),
                child: ListTile(
                  leading: const Icon(Icons.history, color: Colors.white38),
                  title: Text(
                    query,
                    style: const TextStyle(color: Colors.white70, fontSize: 15),
                  ),
                  trailing: IconButton(
                    icon: const Icon(Icons.north_west, color: Colors.white24, size: 18),
                    onPressed: () {
                      _controller.text = query;
                      setState(() {});
                    },
                  ),
                  onTap: () {
                    _controller.text = query;
                    search.search(query);
                  },
                ),
              ).animate().fadeIn(delay: (index * 30).ms);
            },
          ),
        ),
      ],
    );
  }
}
