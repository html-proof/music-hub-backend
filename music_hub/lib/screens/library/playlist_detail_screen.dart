
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../providers/player_provider.dart';
import '../../models/models.dart';
import '../../widgets/song_tile.dart';

class PlaylistDetailScreen extends StatelessWidget {
  final Playlist playlist;

  const PlaylistDetailScreen({super.key, required this.playlist});

  @override
  Widget build(BuildContext context) {
    final player = Provider.of<PlayerProvider>(context, listen: false);

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 200,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                playlist.name,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Color(0xFF7C3AED), Color(0xFF0A0A0F)],
                  ),
                ),
                child: Center(
                  child: Icon(
                    Icons.queue_music_rounded,
                    size: 80,
                    color: Colors.white.withOpacity(0.3),
                  ),
                ),
              ),
            ),
          ),

          // Playlist actions
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Text(
                    '${playlist.songs.length} songs',
                    style: TextStyle(color: Colors.grey[400]),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.shuffle_rounded, color: Colors.white70),
                    onPressed: playlist.songs.isNotEmpty
                        ? () {
                            final shuffled = List<Song>.from(playlist.songs)..shuffle();
                            player.playQueue(shuffled);
                          }
                        : null,
                  ),
                  const SizedBox(width: 8),
                  ElevatedButton.icon(
                    onPressed: playlist.songs.isNotEmpty
                        ? () => player.playQueue(playlist.songs)
                        : null,
                    icon: const Icon(Icons.play_arrow_rounded),
                    label: const Text('Play All'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF7C3AED),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(24),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Songs
          playlist.songs.isEmpty
              ? SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.all(40),
                    child: Center(
                      child: Column(
                        children: [
                          Icon(Icons.music_off, size: 48, color: Colors.grey[800]),
                          const SizedBox(height: 12),
                          Text('No songs in this playlist',
                              style: TextStyle(color: Colors.grey[600])),
                        ],
                      ),
                    ),
                  ),
                )
              : SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final song = playlist.songs[index];
                      return SongTile(
                        song: song,
                        onTap: () => player.playQueue(playlist.songs, startIndex: index),
                      ).animate().fadeIn(delay: (index * 30).ms);
                    },
                    childCount: playlist.songs.length,
                  ),
                ),

          const SliverToBoxAdapter(child: SizedBox(height: 120)),
        ],
      ),
    );
  }
}
