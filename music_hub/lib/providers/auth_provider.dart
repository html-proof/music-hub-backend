
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../config/constants.dart';
import 'package:dio/dio.dart';

enum AuthStatus { unknown, authenticated, unauthenticated, loading, needsOnboarding }

class AuthProvider extends ChangeNotifier {
  final ApiService _apiService;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();
  
  AuthStatus _status = AuthStatus.unknown;
  UserProfile? _user;
  String? _error;
  bool _needsOnboarding = false;

  AuthStatus get status => _status;
  UserProfile? get user => _user;
  String? get error => _error;
  bool get isAuthenticated => _status == AuthStatus.authenticated || _status == AuthStatus.needsOnboarding;
  bool get needsOnboarding => _needsOnboarding;

  AuthProvider(this._apiService);

  Future<void> init() async {
    _status = AuthStatus.loading;
    notifyListeners();

    _auth.authStateChanges().listen((User? firebaseUser) async {
       if (firebaseUser == null) {
         _status = AuthStatus.unauthenticated;
         _user = null;
         notifyListeners();
       } else {
         try {
           final token = await firebaseUser.getIdToken();
           if (token != null) {
              await _storage.write(key: AppConstants.tokenKey, value: token);
              _user = UserProfile(
                  uid: firebaseUser.uid, 
                  email: firebaseUser.email ?? "", 
                  name: firebaseUser.displayName,
                  photoUrl: firebaseUser.photoURL,
              );
              
              // Check onboarding status
              await _checkOnboarding();
           }
         } catch (e) {
           _status = AuthStatus.authenticated;
           _user = UserProfile(
              uid: firebaseUser.uid, 
              email: firebaseUser.email ?? "", 
              name: firebaseUser.displayName,
              photoUrl: firebaseUser.photoURL,
           );
         }
         notifyListeners();
       }
    });
  }

  Future<void> _checkOnboarding() async {
    try {
      final data = await _apiService.checkOnboarding();
      _needsOnboarding = data['needs_onboarding'] ?? true;
      _status = _needsOnboarding ? AuthStatus.needsOnboarding : AuthStatus.authenticated;
    } catch (e) {
      // If check fails, assume authenticated (onboarding optional)
      _status = AuthStatus.authenticated;
      _needsOnboarding = false;
    }
  }

  void completeOnboarding() {
    _needsOnboarding = false;
    _status = AuthStatus.authenticated;
    notifyListeners();
  }

  Future<bool> signInWithGoogle() async {
    _status = AuthStatus.loading;
    _error = null;
    notifyListeners();

    try {
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) {
        _status = AuthStatus.unauthenticated;
        notifyListeners();
        return false;
      }

      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
      final AuthCredential credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final UserCredential userCredential = await _auth.signInWithCredential(credential);
      final User? user = userCredential.user;

      if (user != null) {
        final idToken = await user.getIdToken();
        return await _backendLogin(idToken!);
      }
      
      return false;

    } catch (e) {
      _error = e.toString();
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      return false;
    }
  }

  Future<bool> _backendLogin(String idToken) async {
    try {
      final data = await _apiService.login(idToken);
      await _storage.write(key: AppConstants.tokenKey, value: idToken);
      
      _user = UserProfile(
        uid: data['user_id'] ?? '',
        email: data['email'] ?? '',
        name: data['display_name'],
        photoUrl: _user?.photoUrl,
      );
      _status = AuthStatus.authenticated;
      notifyListeners();

      // Check onboarding after login
      await _checkOnboarding();
      notifyListeners();

      return true;
    } on DioException catch (_) {
      // Backend might be down — still allow auth since Firebase is valid
      _status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      _status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    }
  }

  Future<void> refreshProfile() async {
    try {
      final profile = await _apiService.getProfile();
      _user = profile;
      notifyListeners();
    } catch (_) {}
  }

  Future<void> logout() async {
    await _apiService.logout();
    await _storage.delete(key: AppConstants.tokenKey);
    await _googleSignIn.signOut();
    await _auth.signOut();
    _user = null;
    _needsOnboarding = false;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }
}
