import { state } from './state.js';

export const TRANSLATIONS_EL = {
  // Sidebar
  'Gesture Controller': 'Έλεγχος Χειρονομιών',
  'Dashboard': 'Πίνακας',
  'Camera': 'Κάμερα',
  'Settings': 'Ρυθμίσεις',
  'Connecting…': 'Σύνδεση…',
  'Connected': 'Συνδεδεμένο',
  'Disconnected': 'Αποσυνδεδεμένο',

  // Dashboard
  'Gesture Mappings': 'Αντιστοιχίσεις Χειρονομιών',
  '↻ Sync': '↻ Συγχρονισμός',
  'No gesture mappings yet': 'Δεν υπάρχουν αντιστοιχίσεις ακόμη',
  'Tap the + button to connect a device and assign a gesture.': 'Πατήστε το κουμπί + για να συνδέσετε μια συσκευή και να αναθέσετε μια χειρονομία.',
  'mapping configured': 'αντιστοίχιση διαμορφωμένη',
  'mappings configured': 'αντιστοιχίσεις διαμορφωμένες',
  'Synced': 'Συγχρονισμένο',
  'Pending sync': 'Εκκρεμεί συγχρονισμός',
  'Local PC': 'Τοπικός Υπολογιστής',

  // Card menu / toasts
  'Edit': 'Επεξεργασία',
  'Delete': 'Διαγραφή',
  'Mapping deleted': 'Η αντιστοίχιση διαγράφηκε',
  'Mapping added': 'Η αντιστοίχιση προστέθηκε',
  'Mapping updated': 'Η αντιστοίχιση ενημερώθηκε',
  'Mappings synced': 'Οι αντιστοιχίσεις συγχρονίστηκαν',
  'Sync failed': 'Ο συγχρονισμός απέτυχε',

  // Camera view
  'Live Camera': 'Ζωντανή Κάμερα',
  'Gesture recognition feed': 'Ροή αναγνώρισης χειρονομιών',
  '↻ Refresh': '↻ Ανανέωση',
  'No feed available': 'Δεν υπάρχει διαθέσιμη ροή',
  'Make sure the gesture engine is running': 'Βεβαιωθείτε ότι ο μηχανισμός χειρονομιών λειτουργεί',

  // Settings hub
  'Configure your Sensee hub': 'Διαμορφώστε το Sensee',
  'Home Assistant': 'Home Assistant',
  'URL and access token': 'URL και διακριτικό πρόσβασης',
  'Gesture Settings': 'Ρυθμίσεις Χειρονομιών',
  'Wake gesture, hold duration, active window': 'Χειρονομία αφύπνισης, διάρκεια κράτησης, ενεργό παράθυρο',
  'Camera Settings': 'Ρυθμίσεις Κάμερας',
  'Network camera and stream URL': 'Δικτυακή κάμερα και URL ροής',

  // HA Settings
  '‹ Settings': '‹ Ρυθμίσεις',
  'Loading…': 'Φόρτωση…',
  'Server URL': 'URL Διακομιστή',
  'Long-Lived Access Token': 'Διακριτικό Μακροπρόθεσμης Πρόσβασης',
  'Token saved — enter new to replace': 'Διακριτικό αποθηκεύτηκε — εισάγετε νέο για αντικατάσταση',
  'Paste token here': 'Επικολλήστε το διακριτικό εδώ',
  'Current': 'Τρέχον',
  'Save Configuration': 'Αποθήκευση Διαμόρφωσης',
  'URL is required': 'Απαιτείται URL',
  'Saving…': 'Αποθήκευση…',
  'Home Assistant configured': 'Το Home Assistant διαμορφώθηκε',
  'Failed': 'Απέτυχε',

  // Gesture Settings
  'Wake Gesture': 'Χειρονομία Αφύπνισης',
  'Require a wake gesture before commands': 'Απαιτείται χειρονομία αφύπνισης πριν τις εντολές',
  'Hold Duration': 'Διάρκεια Κράτησης',
  'Active Window': 'Ενεργό Παράθυρο',
  'Save Settings': 'Αποθήκευση Ρυθμίσεων',
  'Gesture settings saved': 'Οι ρυθμίσεις χειρονομιών αποθηκεύτηκαν',

  // Camera Settings
  'Use Network Camera': 'Χρήση Δικτυακής Κάμερας',
  'Stream from RTSP/HTTP instead of local camera': 'Ροή από RTSP/HTTP αντί τοπικής κάμερας',
  'Stream URL': 'URL Ροής',
  '📷 Browse HA Cameras': '📷 Αναζήτηση Καμερών HA',
  'Camera settings saved': 'Οι ρυθμίσεις κάμερας αποθηκεύτηκαν',
  'Could not load HA cameras': 'Δεν ήταν δυνατή η φόρτωση καμερών HA',

  // Camera picker modal
  'Select Camera': 'Επιλογή Κάμερας',
  'No cameras found': 'Δεν βρέθηκαν κάμερες',
  'Camera selected': 'Η κάμερα επιλέχθηκε',

  // Wizard
  'Select Device Type': 'Επιλογή Τύπου Συσκευής',
  'Connection Method': 'Μέθοδος Σύνδεσης',
  'Smart Home Device': 'Έξυπνη Συσκευή',
  'Connect via Home Assistant': 'Σύνδεση μέσω Home Assistant',
  'Classic / IR Device': 'Κλασική / IR Συσκευή',
  'Select brand from library': 'Επιλογή μάρκας από τη βιβλιοθήκη',
  'Pair New TV': 'Σύζευξη νέας TV',
  'Discover and pair via Home Assistant': 'Ανακάλυψη και σύζευξη μέσω Home Assistant',

  'Select HA Device': 'Επιλογή Συσκευής HA',
  'Loading devices…': 'Φόρτωση συσκευών…',
  'devices found': 'συσκευές βρέθηκαν',
  'Make sure Home Assistant is configured and devices are added.': 'Βεβαιωθείτε ότι το Home Assistant έχει ρυθμιστεί και έχουν προστεθεί συσκευές.',
  'Search devices…': 'Αναζήτηση συσκευών…',
  'Failed to load devices': 'Αποτυχία φόρτωσης συσκευών',

  'Select Brand': 'Επιλογή Μάρκας',
  'Search brands…': 'Αναζήτηση μαρκών…',

  'Edit Mapping': 'Επεξεργασία Αντιστοίχισης',
  'Configure Action': 'Διαμόρφωση Ενέργειας',
  'Action': 'Ενέργεια',
  'Gesture': 'Χειρονομία',
  'Hand': 'Χέρι',
  '⚠ This gesture + hand combination is already assigned to another mapping.': '⚠ Αυτός ο συνδυασμός χειρονομίας + χεριού έχει ήδη αντιστοιχιστεί σε άλλη αντιστοίχιση.',
  'Cancel': 'Ακύρωση',
  'Save Changes': 'Αποθήκευση Αλλαγών',
  'Add Mapping': 'Προσθήκη Αντιστοίχισης',

  // Pairing
  'Pair New Device': 'Σύζευξη Νέας Συσκευής',
  'Discovering devices…': 'Ανακάλυψη συσκευών…',
  'No devices discovered. Make sure devices are in pairing mode.': 'Δεν ανακαλύφθηκαν συσκευές. Βεβαιωθείτε ότι οι συσκευές είναι σε λειτουργία σύζευξης.',
  'Starting pairing…': 'Έναρξη σύζευξης…',
  'Enter PIN shown on device': 'Εισάγετε το PIN που εμφανίζεται στη συσκευή',
  'Pair': 'Σύζευξη',
  'Device paired successfully!': 'Η συσκευή συζεύχθηκε επιτυχώς!',
  'Pairing failed — check PIN': 'Σύζευξη απέτυχε — ελέγξτε το PIN',
  'Error': 'Σφάλμα',

  // Gesture / Hand labels
  'Index + Thumb': 'Δείκτης + Αντίχειρας',
  'Middle + Thumb': 'Μέσος + Αντίχειρας',
  'Open Palm': 'Ανοιχτή Παλάμη',
  'Fist': 'Γροθιά',
  'Left': 'Αριστερό',
  'Right': 'Δεξί',
  'Both': 'Και τα δύο',

  // Actions
  'Turn on': 'Ενεργοποίηση',
  'Turn off': 'Απενεργοποίηση',
  'Increase volume': 'Αύξηση έντασης',
  'Decrease volume': 'Μείωση έντασης',
  'Open Spotify': 'Άνοιγμα Spotify',
  'Open YouTube': 'Άνοιγμα YouTube',
  'Close Window': 'Κλείσιμο Παραθύρου',
  'Open Browser': 'Άνοιγμα Φυλλομετρητή',

  // Device types
  'Light': 'Φως',
  'Fan': 'Ανεμιστήρας',
  'PC': 'Υπολογιστής',
};

export function t(key) {
  if (state.lang === 'el') return TRANSLATIONS_EL[key] ?? key;
  return key;
}
