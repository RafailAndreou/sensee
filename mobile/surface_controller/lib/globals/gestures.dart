const supportedGestures = [
  'Open Palm',
  'Fist',
  'Thumb+Index',
  'Thumb+Middle',
  'Thumb+Ring',
  'Thumb+Pinky',
  'Victory',
  'Thumb Up',
  'Thumb Down',
  'Pointing Up',
  'ILoveYou',
];
String _key(String value) =>
    (value
            .trim()
            .toLowerCase()
            .replaceAll(RegExp(r'[_+]'), ' ')
            .split(RegExp(r'\s+'))
          ..sort())
        .join(' ');
final _names = {
  for (final name in supportedGestures) _key(name): name,
  _key('Closed Fist'): 'Fist',
  _key('Open Hand'): 'Open Palm',
  _key('Thumbs+Index'): 'Thumb+Index',
};
String normalizeGestureName(String value) =>
    _names[_key(value)] ?? value.trim();
String wakeGestureName(String value) {
  final name = normalizeGestureName(value);
  return supportedGestures.contains(name) ? name : 'Open Palm';
}
