
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../providers/player_provider.dart';
import '../../providers/library_provider.dart';

class PlayerScreen extends StatelessWidget {
  const PlayerScreen({super.key});

  String _formatDuration(Duration d) {
    final minutes = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final seconds = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    final player = Provider.of<PlayerProvider>(context);
    final library = Provider.of<LibraryProvider>(context);
    final song = player.currentSong;

    if (song == null) {
      return const Scaffold(body: Center(child: Text('No song playing')));
    }

    final isLiked = library.isSongLiked(song.id);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF1A0A2E), Color(0xFF0A0A0F)],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // Top bar
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.keyboard_arrow_down, size: 32, color: Colors.white),
                      onPressed: () => Navigator.pop(context),
                    ),
                    const Expanded(
                      child: Text(
                        'NOW PLAYING',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Colors.white54,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 2,
                        ),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.more_vert, color: Colors.white54),
                      onPressed: () => _showOptionsSheet(context, song),
                    ),
                  ],
                ),
              ),
              
              const Spacer(),
              
              // Artwork
              Container(
                width: 300,
                height: 300,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF7C3AED).withOpacity(0.3),
                      blurRadius: 40,
                      spreadRadius: 5,
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(20),
                  child: CachedNetworkImage(
                    imageUrl: song.thumbnailUrl,
                    fit: BoxFit.cover,
                    placeholder: (_, __) => Container(
                      color: const Color(0xFF1E1E2E),
                      child: const Icon(Icons.music_note, size: 80, color: Colors.white24),
                    ),
                    errorWidget: (_, __, ___) => Container(
                      color: const Color(0xFF1E1E2E),
                      child: const Icon(Icons.music_note, size: 80, color: Colors.white24),
                    ),
                  ),
                ),
              ),
              
              const Spacer(),

              // Song info + like
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            song.title,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            song.artist,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(fontSize: 16, color: Colors.grey[400]),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: Icon(
                        isLiked ? Icons.favorite : Icons.favorite_border,
                        color: isLiked ? const Color(0xFFEC4899) : Colors.white54,
                        size: 28,
                      ),
                      onPressed: () => library.toggleLike(song),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // Seek bar
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 32),
                child: Column(
                  children: [
                    SliderTheme(
                      data: const SliderThemeData(
                        trackHeight: 3,
                        thumbShape: RoundSliderThumbShape(enabledThumbRadius: 6),
                        overlayShape: RoundSliderOverlayShape(overlayRadius: 14),
                      ),
                      child: Slider(
                        value: player.position.inSeconds.toDouble().clamp(
                            0, player.duration.inSeconds.toDouble().clamp(1, double.infinity)),
                        min: 0,
                        max: player.duration.inSeconds.toDouble().clamp(1, double.infinity),
                        activeColor: const Color(0xFF7C3AED),
                        inactiveColor: Colors.white12,
                        onChanged: (v) => player.seek(Duration(seconds: v.toInt())),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            _formatDuration(player.position),
                            style: TextStyle(color: Colors.grey[500], fontSize: 13),
                          ),
                          Text(
                            _formatDuration(player.duration),
                            style: TextStyle(color: Colors.grey[500], fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Controls
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    IconButton(
                      icon: Icon(
                        Icons.shuffle_rounded,
                        color: player.isShuffled ? const Color(0xFF7C3AED) : Colors.white54,
                      ),
                      onPressed: player.toggleShuffle,
                    ),
                    IconButton(
                      icon: const Icon(Icons.skip_previous_rounded, color: Colors.white, size: 36),
                      onPressed: player.skipToPrevious,
                    ),
                    Container(
                      width: 72,
                      height: 72,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          colors: [Color(0xFF7C3AED), Color(0xFFEC4899)],
                        ),
                      ),
                      child: player.isLoading
                          ? const Padding(
                              padding: EdgeInsets.all(20),
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : IconButton(
                              icon: Icon(
                                player.isPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded,
                                color: Colors.white,
                                size: 36,
                              ),
                              onPressed: player.togglePlay,
                            ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.skip_next_rounded, color: Colors.white, size: 36),
                      onPressed: player.skipToNext,
                    ),
                    IconButton(
                      icon: Icon(
                        player.repeatMode == RepeatMode.one
                            ? Icons.repeat_one_rounded
                            : Icons.repeat_rounded,
                        color: player.repeatMode != RepeatMode.off
                            ? const Color(0xFF7C3AED)
                            : Colors.white54,
                      ),
                      onPressed: player.toggleRepeat,
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  void _showOptionsSheet(BuildContext context, dynamic song) {
    final library = Provider.of<LibraryProvider>(context, listen: false);
    final player = Provider.of<PlayerProvider>(context, listen: false);

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1E1E2E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40, height: 4,
              decoration: BoxDecoration(
                color: Colors.grey[700],
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 16),
            ListTile(
              leading: const Icon(Icons.favorite_border, color: Colors.white70),
              title: const Text('Like Song', style: TextStyle(color: Colors.white)),
              onTap: () {
                library.toggleLike(song);
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.playlist_add, color: Colors.white70),
              title: const Text('Add to Playlist', style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(context);
                _showAddToPlaylistDialog(context, song, library);
              },
            ),
            ListTile(
              leading: const Icon(Icons.queue_music, color: Colors.white70),
              title: const Text('Add to Queue', style: TextStyle(color: Colors.white)),
              onTap: () {
                player.addToQueue(song);
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Added to queue'),
                    backgroundColor: Color(0xFF7C3AED),
                    duration: Duration(seconds: 1),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showAddToPlaylistDialog(BuildContext context, dynamic song, LibraryProvider library) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1E1E2E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Add to Playlist',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 16),
            if (library.playlists.isEmpty)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Center(
                  child: Text('No playlists yet', style: TextStyle(color: Colors.white54)),
                ),
              )
            else
              ...library.playlists.map((p) => ListTile(
                leading: const Icon(Icons.queue_music, color: Color(0xFF7C3AED)),
                title: Text(p.name, style: const TextStyle(color: Colors.white)),
                onTap: () {
                  library.addSongToPlaylist(p.id, song.id);
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Added to "${p.name}"'),
                      backgroundColor: const Color(0xFF7C3AED),
                    ),
                  );
                },
              )),
          ],
        ),
      ),
    );
  }
}
