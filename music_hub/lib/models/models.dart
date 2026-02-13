
/// All data models for Music Hub, matching the backend Pydantic schemas.

class Song {
  final String id;
  final String title;
  final String artist;
  final String thumbnailUrl;
  final String? audioUrl;
  final int durationSeconds;

  Song({
    required this.id,
    required this.title,
    required this.artist,
    required this.thumbnailUrl,
    this.audioUrl,
    this.durationSeconds = 0,
  });

  factory Song.fromJson(Map<String, dynamic> json) {
    return Song(
      id: json['id'] ?? json['video_id'] ?? '',
      title: json['title'] ?? 'Unknown',
      artist: json['artist'] ?? json['channel'] ?? 'Unknown',
      thumbnailUrl: json['thumbnailUrl'] ?? json['thumbnail'] ??
          (json['video_id'] != null
              ? 'https://i.ytimg.com/vi/${json['video_id']}/hqdefault.jpg'
              : ''),
      audioUrl: json['audioUrl'] ?? json['stream_url'],
      durationSeconds: json['durationSeconds'] ?? json['duration'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'artist': artist,
    'thumbnailUrl': thumbnailUrl,
    'audioUrl': audioUrl ?? '',
    'durationSeconds': durationSeconds,
  };
}

class Playlist {
  final String id;
  final String name;
  final List<Song> songs;
  final DateTime? createdAt;

  Playlist({
    required this.id,
    required this.name,
    this.songs = const [],
    this.createdAt,
  });

  factory Playlist.fromJson(Map<String, dynamic> json) {
    return Playlist(
      id: json['id'] ?? json['playlist_id'] ?? '',
      name: json['name'] ?? '',
      songs: (json['songs'] as List?)
          ?.map((e) => e is Map<String, dynamic> ? Song.fromJson(e) : null)
          .whereType<Song>()
          .toList() ?? [],
      createdAt: json['createdAt'] != null || json['created_at'] != null
          ? DateTime.tryParse(json['createdAt'] ?? json['created_at'] ?? '')
          : null,
    );
  }
}

class AutoPlaylist {
  final String playlistId;
  final String name;
  final String description;
  final List<Song> songs;
  final int songCount;
  final String algorithm;
  final String? createdAt;

  AutoPlaylist({
    required this.playlistId,
    required this.name,
    this.description = '',
    this.songs = const [],
    this.songCount = 0,
    required this.algorithm,
    this.createdAt,
  });

  factory AutoPlaylist.fromJson(Map<String, dynamic> json) {
    return AutoPlaylist(
      playlistId: json['playlist_id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      songs: (json['songs'] as List?)
          ?.map((e) => e is Map<String, dynamic> ? Song.fromJson(e) : null)
          .whereType<Song>()
          .toList() ?? [],
      songCount: json['song_count'] ?? 0,
      algorithm: json['algorithm'] ?? 'smart',
      createdAt: json['created_at'],
    );
  }
}

class UserProfile {
  final String uid;
  final String email;
  final String? name;
  final String? photoUrl;
  final String? language;
  final List<String> moods;
  final UserStats? stats;
  final bool isOnboarded;

  UserProfile({
    required this.uid,
    required this.email,
    this.name,
    this.photoUrl,
    this.language,
    this.moods = const [],
    this.stats,
    this.isOnboarded = false,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      uid: json['uid'] ?? json['user_id'] ?? '',
      email: json['email'] ?? '',
      name: json['name'] ?? json['display_name'] ?? json['displayName'],
      photoUrl: json['photoUrl'] ?? json['photo_url'],
      language: json['language'],
      moods: (json['moods'] as List?)?.cast<String>() ?? [],
      stats: json['stats'] != null ? UserStats.fromJson(json['stats']) : null,
      isOnboarded: json['is_onboarded'] ?? json['onboarding_complete'] ?? false,
    );
  }
}

class UserStats {
  final int totalSearches;
  final int totalPlays;
  final int totalSkips;
  final int totalCompletes;

  UserStats({
    this.totalSearches = 0,
    this.totalPlays = 0,
    this.totalSkips = 0,
    this.totalCompletes = 0,
  });

  factory UserStats.fromJson(Map<String, dynamic> json) {
    return UserStats(
      totalSearches: json['total_searches'] ?? 0,
      totalPlays: json['total_plays'] ?? 0,
      totalSkips: json['total_skips'] ?? 0,
      totalCompletes: json['total_completes'] ?? 0,
    );
  }
}

class PlayHistoryItem {
  final String playId;
  final String videoId;
  final String title;
  final String artist;
  final String status; // playing, skipped, completed
  final int duration;
  final int playDuration;
  final String playedAt;

  PlayHistoryItem({
    required this.playId,
    required this.videoId,
    required this.title,
    this.artist = '',
    this.status = 'playing',
    this.duration = 0,
    this.playDuration = 0,
    required this.playedAt,
  });

  factory PlayHistoryItem.fromJson(Map<String, dynamic> json) {
    return PlayHistoryItem(
      playId: json['play_id'] ?? '',
      videoId: json['video_id'] ?? '',
      title: json['title'] ?? '',
      artist: json['artist'] ?? json['channel'] ?? '',
      status: json['status'] ?? 'playing',
      duration: json['duration'] ?? 0,
      playDuration: json['play_duration'] ?? 0,
      playedAt: json['played_at'] ?? '',
    );
  }

  Song toSong() => Song(
    id: videoId,
    title: title,
    artist: artist,
    thumbnailUrl: 'https://i.ytimg.com/vi/$videoId/hqdefault.jpg',
    durationSeconds: duration,
  );
}

class KeywordData {
  final String keyword;
  final double weight;
  final int count;

  KeywordData({
    required this.keyword,
    this.weight = 0,
    this.count = 0,
  });

  factory KeywordData.fromJson(Map<String, dynamic> json) {
    return KeywordData(
      keyword: json['keyword'] ?? '',
      weight: (json['weight'] ?? 0).toDouble(),
      count: json['count'] ?? 0,
    );
  }
}

class TopArtist {
  final String artist;
  final int count;

  TopArtist({required this.artist, required this.count});

  factory TopArtist.fromJson(Map<String, dynamic> json) {
    return TopArtist(
      artist: json['artist'] ?? '',
      count: json['count'] ?? 0,
    );
  }
}

class UserInsights {
  final List<KeywordData> topKeywords;
  final List<TopArtist> topArtists;
  final List<PlayHistoryItem> recentPlays;

  UserInsights({
    this.topKeywords = const [],
    this.topArtists = const [],
    this.recentPlays = const [],
  });

  factory UserInsights.fromJson(Map<String, dynamic> json) {
    return UserInsights(
      topKeywords: (json['top_keywords'] as List?)
          ?.map((e) => KeywordData.fromJson(e))
          .toList() ?? [],
      topArtists: (json['top_artists'] as List?)
          ?.map((e) => TopArtist.fromJson(e))
          .toList() ?? [],
      recentPlays: (json['recent_plays'] as List?)
          ?.map((e) => PlayHistoryItem.fromJson(e))
          .toList() ?? [],
    );
  }
}

class RecommendationSection {
  final String title;
  final String icon;
  final List<Song> songs;

  RecommendationSection({
    required this.title,
    required this.icon,
    this.songs = const [],
  });
}
