
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/models.dart';

class SongTile extends StatelessWidget {
  final Song song;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;
  final Widget? trailing;

  const SongTile({
    super.key,
    required this.song,
    required this.onTap,
    this.onLongPress,
    this.trailing,
  });

  String _formatDuration(int seconds) {
    if (seconds <= 0) return '';
    final m = (seconds ~/ 60).toString().padLeft(2, '0');
    final s = (seconds % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: SizedBox(
          width: 52,
          height: 52,
          child: CachedNetworkImage(
            imageUrl: song.thumbnailUrl,
            fit: BoxFit.cover,
            placeholder: (_, __) => Container(
              color: Colors.grey[900],
              child: const Icon(Icons.music_note, color: Colors.white24, size: 24),
            ),
            errorWidget: (_, __, ___) => Container(
              color: Colors.grey[900],
              child: const Icon(Icons.music_note, color: Colors.white24, size: 24),
            ),
          ),
        ),
      ),
      title: Text(
        song.title,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: const TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 15,
          color: Colors.white,
        ),
      ),
      subtitle: Text(
        song.artist,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
        style: TextStyle(fontSize: 13, color: Colors.grey[500]),
      ),
      trailing: trailing ?? (song.durationSeconds > 0
          ? Text(
              _formatDuration(song.durationSeconds),
              style: TextStyle(color: Colors.grey[600], fontSize: 13),
            )
          : const Icon(Icons.play_arrow, color: Colors.white38, size: 20)),
      onTap: onTap,
      onLongPress: onLongPress,
    );
  }
}
