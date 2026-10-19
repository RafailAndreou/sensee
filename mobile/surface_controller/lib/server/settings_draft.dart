/// A late load may populate a form only if the user has not edited it meanwhile.
class SettingsDraft {
  int _revision = 0;
  int get revision => _revision;
  void edited() {
    _revision++;
  }

  bool isCurrent(int revision) => revision == _revision;
}
