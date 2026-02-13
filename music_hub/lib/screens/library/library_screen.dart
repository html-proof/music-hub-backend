
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../providers/library_provider.dart';
import '../../providers/player_provider.dart';
import '../../services/api_service.dart';
import 'playlist_detail_screen.dart';

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    Future.microtask(() {
      Provider.of<LibraryProvider>(context, listen: false).fetchAll();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Your Library',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 24),
        ),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: const Color(0xFF7C3AED),
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white54,
          tabs: const [
            Tab(text: 'Playlists'),
            Tab(text: 'History'),
            Tab(text: 'Auto Mix'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _PlaylistsTab(),
          _HistoryTab(),
          _AutoPlaylistTab(),
        ],
      ),
    );
  }
}

class _PlaylistsTab extends StatelessWidget {
  void _showCreatePlaylistDialog(BuildContext context) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E2E),
        title: const Text('Create Playlist', style: TextStyle(color: Colors.white)),
        content: TextField(
          controller: controller,
          autofocus: true,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: 'Playlist name',
            hintStyle: TextStyle(color: Colors.grey[500]),
            enabledBorder: UnderlineInputBorder(
              borderSide: BorderSide(color: Colors.grey[700]!),
            ),
            focusedBorder: const UnderlineInputBorder(
              borderSide: BorderSide(color: Color(0xFF7C3AED)),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
          ),
          TextButton(
            onPressed: () {
              if (controller.text.trim().isNotEmpty) {
                Provider.of<LibraryProvider>(ctx, listen: false)
                    .createPlaylist(controller.text.trim());
                Navigator.pop(ctx);
              }
            },
            child: const Text('Create', style: TextStyle(color: Color(0xFF7C3AED))),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final library = Provider.of<LibraryProvider>(context);

    if (library.isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF7C3AED)));
    }

    return Column(
      children: [
        // Create Playlist Button
        Padding(
          padding: const EdgeInsets.all(16),
          child: InkWell(
            onTap: () => _showCreatePlaylistDialog(context),
            borderRadius: BorderRadius.circular(12),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFF7C3AED).withOpacity(0.2),
                    const Color(0xFFEC4899).withOpacity(0.1),
                  ],
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white10),
              ),
              child: const Row(
                children: [
                  Icon(Icons.add_rounded, color: Color(0xFF7C3AED), size: 28),
                  SizedBox(width: 12),
                  Text(
                    'Create New Playlist',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                      fontSize: 16,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),

        // Playlists List
        Expanded(
          child: library.playlists.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.library_music_rounded, size: 64, color: Colors.grey[800]),
                      const SizedBox(height: 12),
                      Text('No playlists yet', style: TextStyle(color: Colors.grey[600])),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.only(bottom: 120),
                  itemCount: library.playlists.length,
                  itemBuilder: (context, index) {
                    final playlist = library.playlists[index];
                    return ListTile(
                      leading: Container(
                        width: 50,
                        height: 50,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFF7C3AED), Color(0xFFEC4899)],
                          ),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.queue_music, color: Colors.white),
                      ),
                      title: Text(playlist.name, style: const TextStyle(fontWeight: FontWeight.w600)),
                      subtitle: Text('${playlist.songs.length} songs',
                          style: TextStyle(color: Colors.grey[500])),
                      trailing: const Icon(Icons.chevron_right, color: Colors.white38),
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => PlaylistDetailScreen(playlist: playlist),
                        ),
                      ),
                    ).animate().fadeIn(delay: (index * 50).ms);
                  },
                ),
        ),
      ],
    );
  }
}

class _HistoryTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final library = Provider.of<LibraryProvider>(context);
    final player = Provider.of<PlayerProvider>(context, listen: false);

    if (library.isLoading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF7C3AED)));
    }

    if (library.playHistory.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.history, size: 64, color: Colors.grey[800]),
            const SizedBox(height: 12),
            Text('No listening history yet', style: TextStyle(color: Colors.grey[600])),
            const SizedBox(height: 8),
            Text('Your recently played songs will appear here',
                style: TextStyle(color: Colors.grey[700], fontSize: 13)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.only(top: 8, bottom: 120),
      itemCount: library.playHistory.length,
      itemBuilder: (context, index) {
        final item = library.playHistory[index];
        return ListTile(
          leading: ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Image.network(
              'https://i.ytimg.com/vi/${item.videoId}/default.jpg',
              width: 50,
              height: 50,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => Container(
                width: 50, height: 50,
                color: Colors.grey[900],
                child: const Icon(Icons.music_note, color: Colors.white24),
              ),
            ),
          ),
          title: Text(item.title, maxLines: 1, overflow: TextOverflow.ellipsis),
          subtitle: Text(
            item.artist.isNotEmpty ? item.artist : 'Unknown',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(color: Colors.grey[500]),
          ),
          trailing: Icon(
            item.status == 'completed'
                ? Icons.check_circle
                : item.status == 'skipped'
                    ? Icons.skip_next
                    : Icons.play_arrow,
            color: item.status == 'completed'
                ? Colors.green
                : Colors.grey[600],
            size: 20,
          ),
          onTap: () => player.playSong(item.toSong()),
        ).animate().fadeIn(delay: (index * 20).ms);
      },
    );
  }
}

class _AutoPlaylistTab extends StatelessWidget {
  static const algorithms = [
    ('✨ Smart Mix', 'smart'),
    ('🔥 Most Played', 'most_played'),
    ('💖 Liked Based', 'liked_based'),
    ('🎤 Artist Mix', 'artist_based'),
    ('🌈 Mood Mix', 'mood_mix'),
  ];

  @override
  Widget build(BuildContext context) {
    final library = Provider.of<LibraryProvider>(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Generate buttons
          const Text(
            'Generate Playlist',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: algorithms.map((algo) {
              return ActionChip(
                label: Text(algo.$1),
                backgroundColor: const Color(0xFF1E1E2E),
                side: const BorderSide(color: Colors.white10),
                labelStyle: const TextStyle(color: Colors.white, fontSize: 13),
                onPressed: () async {
                  final result = await library.generateAutoPlaylist(algorithm: algo.$2);
                  if (result != null && context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Created "${result.name}" with ${result.songs.length} songs'),
                        backgroundColor: const Color(0xFF7C3AED),
                      ),
                    );
                  }
                },
              );
            }).toList(),
          ),

          const SizedBox(height: 24),
          if (library.autoPlaylists.isNotEmpty) ...[
            const Text(
              'Your Auto Playlists',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 12),
            ...library.autoPlaylists.map((ap) => ListTile(
              leading: Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFEC4899), Color(0xFF7C3AED)],
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.auto_awesome, color: Colors.white),
              ),
              title: Text(ap.name, style: const TextStyle(fontWeight: FontWeight.w600)),
              subtitle: Text('${ap.songCount} songs • ${ap.algorithm}',
                  style: TextStyle(color: Colors.grey[500], fontSize: 13)),
              onTap: () async {
                final full = await Provider.of<ApiService>(context, listen: false)
                    .getAutoPlaylist(ap.playlistId);
                if (context.mounted && full.songs.isNotEmpty) {
                  final player = Provider.of<PlayerProvider>(context, listen: false);
                  player.playQueue(full.songs);
                }
              },
            )),
          ] else
            Padding(
              padding: const EdgeInsets.only(top: 40),
              child: Center(
                child: Column(
                  children: [
                    Icon(Icons.auto_awesome, size: 48, color: Colors.grey[800]),
                    const SizedBox(height: 12),
                    Text(
                      'Generate a playlist based on your taste',
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
