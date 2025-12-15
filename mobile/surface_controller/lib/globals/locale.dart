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
    'playMusicAction': 'Play Music',
    'openAc': 'Open AC',
    'acCold': 'AC:cold',
    'acHot': 'AC:Hot',
    'tvTurnOn': 'TV:Turn On',
    'tvTurnOff': 'TV:Turn Off',
    'tvIncreaseVolume': 'TV:Increase Volume',
    'tvDecreaseVolume': 'TV:Decrease Volume',
    'thumbIndex': 'Thumb+Index',
    'thumbMiddle': 'Thumb+Middle',
    'thumbRing': 'Thumb+Ring',
    'sound1': 'Sound1',
    'sound2': 'Sound2',
    'sound3': 'Sound3',
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
    'playMusicAction': 'Αναπαραγωγή Μουσικής',
    'openAc': 'Ανοίξτε AC',
    'acCold': 'AC:Ψύχος',
    'acHot': 'AC:Ζεστό',
    'tvTurnOn': 'TV:Ενεργοποίηση',
    'tvTurnOff': 'TV:Απενεργοποίηση',
    'tvIncreaseVolume': 'TV:Αύξηση Έντασης',
    'tvDecreaseVolume': 'TV:Μείωση Έντασης',
    'thumbIndex': 'Αντίχειρας+Δείκτης',
    'thumbMiddle': 'Αντίχειρας+Μέσο',
    'thumbRing': 'Αντίχειρας+Παράδοξος',
    'sound1': 'Ήχος1',
    'sound2': 'Ήχος2',
    'sound3': 'Ήχος3',
  },
};

String tr(String key, String lang) {
  return _translations[lang]?[key] ?? _translations['en']?[key] ?? key;
}

// Map Greek display text back to English value for configuration
String toEnglishValue(String displayText) {
  // Action options
  if (displayText == 'Αναπαραγωγή Μουσικής') return 'Play Music';
  if (displayText == 'Ανοίξτε AC') return 'Open AC';
  if (displayText == 'AC:Ψύχος') return 'AC:cold';
  if (displayText == 'AC:Ζεστό') return 'AC:Hot';
  if (displayText == 'TV:Ενεργοποίηση') return 'TV:Turn On';
  if (displayText == 'TV:Απενεργοποίηση') return 'TV:Turn Off';
  if (displayText == 'TV:Αύξηση Έντασης') return 'TV:Increase Volume';
  if (displayText == 'TV:Μείωση Έντασης') return 'TV:Decrease Volume';
  // Gesture options
  if (displayText == 'Αντίχειρας+Δείκτης') return 'Thumb+Index';
  if (displayText == 'Αντίχειρας+Μέσο') return 'Thumb+Middle';
  if (displayText == 'Αντίχειρας+Παράδοξος') return 'Thumb+Ring';
  // Sound options
  if (displayText == 'Ήχος1') return 'Sound1';
  if (displayText == 'Ήχος2') return 'Sound2';
  if (displayText == 'Ήχος3') return 'Sound3';
  // If already English or unknown, return as-is
  return displayText;
}

void toggleLanguage() {
  currentLanguage.value = currentLanguage.value == 'en' ? 'el' : 'en';
}
