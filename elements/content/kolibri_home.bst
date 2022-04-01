kind: manual

build-depends:
- freedesktop-sdk.bst:components/python3.bst
- freedesktop-sdk.bst:components/python3-pip.bst
- software/plugins.bst

sources:
- kind: github_release
  repo: learningequality/kolibri
  asset: kolibri-0.15.1-py2.py3-none-any.whl

  url: https://github.com/learningequality/kolibri/releases/download/v0.15.1/kolibri-0.15.1-py2.py3-none-any.whl
  asset_id: '57049082'
config:
  build-commands:
  - echo "Create the kolibri home"
  - python3 -m venv env
  - ./env/bin/pip install kolibri-0.15.1-py2.py3-none-any.whl
  - KOLIBRI_HOME=$PWD/KOLIBRI_HOME ./env/bin/kolibri manage

  - KOLIBRI_HOME=$PWD/KOLIBRI_HOME PYTHONPATH=/plugins ./env/bin/kolibri plugin enable kolibri_explore_plugin
  - KOLIBRI_HOME=$PWD/KOLIBRI_HOME PYTHONPATH=/plugins ./env/bin/kolibri plugin enable kolibri_zim_plugin

  - KOLIBRI_HOME=$PWD/KOLIBRI_HOME PYTHONPATH=/plugins ./env/bin/kolibri plugin enable kolibri.plugins.app
  - KOLIBRI_HOME=$PWD/KOLIBRI_HOME PYTHONPATH=/plugins ./env/bin/kolibri plugin disable kolibri.plugins.learn
  - rm -rf KOLIBRI_HOME/process_cache
  - rm -rf KOLIBRI_HOME/logs
  - rm -rf KOLIBRI_HOME/sessions

  install-commands:
  - cp -r KOLIBRI_HOME %{install-root}/KOLIBRI_HOME
