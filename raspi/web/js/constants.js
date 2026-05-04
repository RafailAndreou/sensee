export const DEVICE_TYPES = ['TV', 'AC', 'Light', 'Fan', 'PC'];

export const DEVICE_META = {
  TV:    { emoji: '📺', bg: 'rgba(59,130,246,0.18)',  accent: '#3b82f6' },
  AC:    { emoji: '❄️', bg: 'rgba(34,197,94,0.18)',   accent: '#22c55e' },
  Light: { emoji: '💡', bg: 'rgba(245,158,11,0.18)',  accent: '#f59e0b' },
  Fan:   { emoji: '🌀', bg: 'rgba(168,85,247,0.18)',  accent: '#a855f7' },
  PC:    { emoji: '💻', bg: 'rgba(99,102,241,0.18)',  accent: '#6366f1' },
};

export const GESTURES = [
  { id: 'Index+Thumb',  label: 'Index + Thumb',  icon: '🤏' },
  { id: 'Middle+Thumb', label: 'Middle + Thumb', icon: '✌️' },
  { id: 'Open Palm',    label: 'Open Palm',      icon: '✋' },
  { id: 'Fist',         label: 'Fist',           icon: '✊' },
];

export const HANDS = [
  { id: 'Left Hand',  label: 'Left',  icon: '🫲' },
  { id: 'Right Hand', label: 'Right', icon: '🫱' },
  { id: 'Both Hands', label: 'Both',  icon: '👐' },
];

export const ACTIONS_BY_TYPE = {
  TV:    ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
  AC:    ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
  Light: ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
  Fan:   ['Turn on', 'Turn off', 'Increase volume', 'Decrease volume'],
  PC:    ['Open Spotify', 'Open YouTube', 'Close Window', 'Open Browser'],
};

export const BRANDS_BY_TYPE = {
  TV:    ['Samsung', 'LG', 'Sony', 'TCL', 'Hisense', 'Philips', 'Panasonic', 'Sharp', 'Vizio', 'Toshiba'],
  AC:    ['Daikin', 'Carrier', 'LG', 'Samsung', 'Mitsubishi', 'Panasonic', 'Hitachi', 'Fujitsu', 'Toshiba', 'Gree'],
  Light: ['Philips Hue', 'Wyze', 'LIFX', 'GE', 'Sengled', 'Nanoleaf', 'Govee', 'Kasa'],
  Fan:   ['Dyson', 'Honeywell', 'Lasko', 'Hunter', 'Vornado', 'Minka Aire', 'Hampton Bay'],
  PC:    ['Custom'],
};
