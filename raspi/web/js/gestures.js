export const SUPPORTED_GESTURES = ['Open Palm', 'Fist', 'Thumb+Index', 'Thumb+Middle',
  'Thumb+Ring', 'Thumb+Pinky', 'Victory', 'Thumb Up', 'Thumb Down', 'Pointing Up', 'ILoveYou'];
const key = value => String(value).trim().toLowerCase().replace(/[_+]/g, ' ').split(/\s+/).sort().join(' ');
const names = new Map(SUPPORTED_GESTURES.map(name => [key(name), name]));
names.set(key('Closed Fist'), 'Fist');
names.set(key('Open Hand'), 'Open Palm');
names.set(key('Thumbs+Index'), 'Thumb+Index');
export function normalizeGestureName(value) { return names.get(key(value)) || String(value).trim(); }
export function wakeGestureName(value) {
  const name = normalizeGestureName(value);
  return SUPPORTED_GESTURES.includes(name) ? name : 'Open Palm';
}
