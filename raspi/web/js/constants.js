import { SUPPORTED_GESTURES } from './gestures.js';
export const DEVICE_TYPES = ['TV', 'AC', 'Light', 'Fan', 'Scene', 'Script', 'PC'];

export const DEVICE_META = {
  Scene: {emoji:'🎬', bg:'#333', accent:'#aaa'}, Script: {emoji:'▶', bg:'#333', accent:'#aaa'},
  TV:    { emoji: '📺', bg: 'rgba(59,130,246,0.18)',  accent: '#3b82f6' },
  AC:    { emoji: '❄️', bg: 'rgba(34,197,94,0.18)',   accent: '#22c55e' },
  Light: { emoji: '💡', bg: 'rgba(245,158,11,0.18)',  accent: '#f59e0b' },
  Fan:   { emoji: '🌀', bg: 'rgba(168,85,247,0.18)',  accent: '#a855f7' },
  PC:    { emoji: '💻', bg: 'rgba(99,102,241,0.18)',  accent: '#6366f1' },
};

export const GESTURES = SUPPORTED_GESTURES.map(id => ({id, label:id, icon:'✋'}));

export const HANDS = [
  { id: 'Left Hand',  label: 'Left',  icon: '🫲' },
  { id: 'Right Hand', label: 'Right', icon: '🫱' },
  { id: 'Both Hands', label: 'Both',  icon: '👐' },
];

export const ACTIONS_BY_TYPE = {
  Scene: ['Activate'], Script: ['Activate'],
  TV:    ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
  AC:    ['Turn on', 'Turn off', 'Temperature 20', 'Temperature 22'],
  Light: ['Turn on', 'Turn off', 'Brightness 25', 'Brightness 50', 'Brightness 100'],
  Fan:   ['Turn on', 'Turn off', 'Fan speed 25', 'Fan speed 50', 'Fan speed 100'],
  PC:    ['Open Spotify', 'Open YouTube', 'Close Window', 'Open Browser'],
};

export const BRANDS_BY_TYPE = {
  Scene: [], Script: [],
  TV:    ['Samsung', 'LG', 'Sony', 'TCL', 'Hisense', 'Philips', 'Panasonic', 'Sharp', 'Vizio', 'Toshiba'],
  AC:    ['Daikin', 'Carrier', 'LG', 'Samsung', 'Mitsubishi', 'Panasonic', 'Hitachi', 'Fujitsu', 'Toshiba', 'Gree'],
  Light: ['Philips Hue', 'Wyze', 'LIFX', 'GE', 'Sengled', 'Nanoleaf', 'Govee', 'Kasa'],
  Fan:   ['Dyson', 'Honeywell', 'Lasko', 'Hunter', 'Vornado', 'Minka Aire', 'Hampton Bay'],
  PC:    ['Custom'],
};
