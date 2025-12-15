import 'package:flutter/foundation.dart';

// Simple in-memory locale store to avoid adding heavy i18n dependencies.
final ValueNotifier<String> currentLanguage = ValueNotifier<String>('en');

const Map<String, Map<String, String>> _translations = {
  'en': {
    'appTitle': 'Sensee Smart Controller',
    'gestureMapping': 'Gesture mapping',
    'liveCamera': 'Live Camera',
    'deviceActions': 'Device Actions',
    'addAction': 'Add Action',
    'applyApiChanges': 'Apply API Changes',
    'action': 'Action',
    'gesture': 'Gesture',
    'playMusic': 'Play Music',
    'gestureHand': 'Gesture Hand',
    'left': 'Left',
    'right': 'Right',
    'both': 'Both',
    'configure': 'Configure',
    'remove': 'Remove',
  },
  'el': {
    'appTitle': 'Sensee Έξυπνος Controller',
    'gestureMapping': 'Χαρτογράφηση',
    'liveCamera': 'Live κάμερα',
    'deviceActions': 'Ενέργειες',
    'addAction': 'Προσθήκη',
    'applyApiChanges': 'Εφαρμογή αλλαγών API',
    'action': 'Ενέργεια',
    'gesture': 'Χειρονομία',
    'playMusic': 'Ήχος',
    'gestureHand': 'Χέρι χειρονομίας',
    'left': 'Αριστερό',
    'right': 'Δεξί',
    'both': 'Δύο',
    'configure': 'Ρύθμιση',
    'remove': 'Αφαίρεση',
  },
};

String tr(String key, String lang) {
  return _translations[lang]?[key] ?? _translations['en']?[key] ?? key;
}

void toggleLanguage() {
  currentLanguage.value = currentLanguage.value == 'en' ? 'el' : 'en';
}
