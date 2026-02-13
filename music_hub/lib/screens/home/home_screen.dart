
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:shimmer/shimmer.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../providers/home_provider.dart';
import '../../providers/player_provider.dart';
import '../../providers/auth_provider.dart';
import '../../models/models.dart';
import '../profile/profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      final auth = Provider.of<AuthProvider>(context, listen: false);
      Provider.of<HomeProvider>(context, listen: false)
          .fetchHomeData(uid: auth.user?.uid);
    });
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  }

  @override
  Widget build(BuildContext context) {
    final homeProvider = Provider.of<HomeProvider>(context);
    final playerProvider = Provider.of<PlayerProvider>(context, listen: false);
    final auth = Provider.of<AuthProvider>(context);

    return Scaffold(
      body: RefreshIndicator(
        color: const Color(0xFF7C3AED),
        onRefresh: () => homeProvider.refresh(uid: auth.user?.uid),
        child: CustomScrollView(
          slivers: [
            // App Bar
            SliverAppBar(
              floating: true,
              snap: true,
              title: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _getGreeting(),
                    style: TextStyle(color: Colors.grey[400], fontSize: 14),
                  ),
                  Text(
                    auth.user?.name ?? 'Music Lover',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 22,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
              actions: [
                GestureDetector(
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const ProfileScreen()),
                  ),
                  child: Container(
                    margin: const EdgeInsets.only(right: 16),
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const LinearGradient(
                        colors: [Color(0xFF7C3AED), Color(0xFFEC4899)],
                      ),
                      image: auth.user?.photoUrl != null
                          ? DecorationImage(
                              image: NetworkImage(auth.user!.photoUrl!),
                              fit: BoxFit.cover,
                            )
                          : null,
                    ),
                    child: auth.user?.photoUrl == null
                        ? const Icon(Icons.person, color: Colors.white, size: 20)
                        : null,
                  ),
                ),
              ],
            ),

            // Content
            if (homeProvider.isLoading)
              SliverToBoxAdapter(child: _buildShimmer())
            else if (homeProvider.error != null)
              SliverToBoxAdapter(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(40),
                    child: Column(
                      children: [
                        const Icon(Icons.music_note, size: 60, color: Colors.white24),
                        const SizedBox(height: 16),
                        Text(
                          homeProvider.error!,
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey[400]),
                        ),
                        const SizedBox(height: 16),
                        TextButton.icon(
                          onPressed: () => homeProvider.refresh(uid: auth.user?.uid),
                          icon: const Icon(Icons.refresh),
                          label: const Text('Refresh'),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            else
              SliverList(
                delegate: SliverChildListDelegate([
                  const SizedBox(height: 8),
                  ...homeProvider.sections.asMap().entries.map((entry) => 
                    _buildSection(entry.value, playerProvider, entry.key)
                  ),
                  const SizedBox(height: 120),
                ]),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(RecommendationSection section, PlayerProvider playerProvider, int index) {
    // Pre-resolve stream URLs for instant playback
    playerProvider.prefetchSongs(section.songs);
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Text(
              section.title,
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),
          SizedBox(
            height: 200,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: section.songs.length,
              itemBuilder: (context, i) {
                final song = section.songs[i];
                return _buildSongCard(song, playerProvider, section.songs);
              },
            ),
          ),
        ],
      ),
    ).animate().fadeIn(delay: (index * 100).ms).slideX(begin: 0.05);
  }

  Widget _buildSongCard(Song song, PlayerProvider playerProvider, List<Song> sectionSongs) {
    return GestureDetector(
      onTap: () => playerProvider.playQueue(sectionSongs, startIndex: sectionSongs.indexOf(song)),
      child: Container(
        width: 150,
        margin: const EdgeInsets.symmetric(horizontal: 4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 150,
              width: 150,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: CachedNetworkImage(
                  imageUrl: song.thumbnailUrl,
                  fit: BoxFit.cover,
                  placeholder: (_, __) => Container(
                    color: Colors.grey[900],
                    child: const Icon(Icons.music_note, color: Colors.white24),
                  ),
                  errorWidget: (_, __, ___) => Container(
                    color: Colors.grey[900],
                    child: const Icon(Icons.music_note, color: Colors.white24),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              song.title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 13,
                color: Colors.white,
              ),
            ),
            Text(
              song.artist,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 12, color: Colors.grey[500]),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildShimmer() {
    return Shimmer.fromColors(
      baseColor: Colors.grey[900]!,
      highlightColor: Colors.grey[800]!,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(width: 200, height: 24, color: Colors.white),
            const SizedBox(height: 16),
            SizedBox(
              height: 180,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: 4,
                itemBuilder: (_, __) => Container(
                  width: 150,
                  height: 150,
                  margin: const EdgeInsets.only(right: 12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 32),
            Container(width: 180, height: 24, color: Colors.white),
            const SizedBox(height: 16),
            SizedBox(
              height: 180,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: 4,
                itemBuilder: (_, __) => Container(
                  width: 150,
                  height: 150,
                  margin: const EdgeInsets.only(right: 12),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
