
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/api_service.dart';
import '../../models/models.dart';
import '../settings/settings_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  UserInsights? _insights;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final api = Provider.of<ApiService>(context, listen: false);
      final insights = await api.getInsights();
      if (mounted) {
        setState(() {
          _insights = insights;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final user = auth.user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings, color: Colors.white70),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const SettingsScreen()),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Avatar + Name
            Container(
              width: 90,
              height: 90,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                  colors: [Color(0xFF7C3AED), Color(0xFFEC4899)],
                ),
                image: user?.photoUrl != null
                    ? DecorationImage(
                        image: NetworkImage(user!.photoUrl!),
                        fit: BoxFit.cover,
                      )
                    : null,
              ),
              child: user?.photoUrl == null
                  ? const Icon(Icons.person, size: 40, color: Colors.white)
                  : null,
            ),
            const SizedBox(height: 16),
            Text(
              user?.name ?? 'Music Lover',
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 4),
            Text(
              user?.email ?? '',
              style: TextStyle(color: Colors.grey[500]),
            ),
            if (user?.language != null) ...[
              const SizedBox(height: 4),
              Text(
                '${user!.language![0].toUpperCase()}${user.language!.substring(1)} • ${user.moods.join(', ')}',
                style: TextStyle(color: Colors.grey[600], fontSize: 13),
              ),
            ],

            const SizedBox(height: 32),

            // Stats
            if (user?.stats != null) _buildStatsRow(user!.stats!),

            const SizedBox(height: 24),

            // Insights
            if (_isLoading)
              const Padding(
                padding: EdgeInsets.all(32),
                child: CircularProgressIndicator(color: Color(0xFF7C3AED)),
              )
            else if (_insights != null) ...[
              if (_insights!.topKeywords.isNotEmpty) ...[
                _sectionTitle('🎵 Top Keywords'),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _insights!.topKeywords.take(15).map((kw) {
                    return Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF7C3AED).withOpacity(0.15),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: const Color(0xFF7C3AED).withOpacity(0.3)),
                      ),
                      child: Text(
                        '${kw.keyword} (${kw.count})',
                        style: const TextStyle(color: Colors.white70, fontSize: 13),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 24),
              ],

              if (_insights!.topArtists.isNotEmpty) ...[
                _sectionTitle('🎤 Top Artists'),
                ...(_insights!.topArtists.take(10).toList().asMap().entries.map((entry) {
                  final a = entry.value;
                  return ListTile(
                    dense: true,
                    leading: CircleAvatar(
                      backgroundColor: const Color(0xFF7C3AED).withOpacity(0.3),
                      radius: 18,
                      child: Text(
                        '${entry.key + 1}',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ),
                    title: Text(a.artist, style: const TextStyle(color: Colors.white)),
                    trailing: Text(
                      '${a.count} plays',
                      style: TextStyle(color: Colors.grey[500]),
                    ),
                  );
                })),
              ],
            ],

            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Align(
        alignment: Alignment.centerLeft,
        child: Text(
          title,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
        ),
      ),
    );
  }

  Widget _buildStatsRow(UserStats stats) {
    return Row(
      children: [
        _statCard('Plays', stats.totalPlays, Icons.play_circle_fill),
        const SizedBox(width: 12),
        _statCard('Searches', stats.totalSearches, Icons.search),
        const SizedBox(width: 12),
        _statCard('Completed', stats.totalCompletes, Icons.check_circle),
      ],
    );
  }

  Widget _statCard(String label, int value, IconData icon) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.white10),
        ),
        child: Column(
          children: [
            Icon(icon, color: const Color(0xFF7C3AED), size: 24),
            const SizedBox(height: 8),
            Text(
              value.toString(),
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 4),
            Text(label, style: TextStyle(color: Colors.grey[500], fontSize: 12)),
          ],
        ),
      ),
    );
  }
}
