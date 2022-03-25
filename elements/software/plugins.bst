kind: manual

build-depends:
- base.bst

sources:
- kind: pypi
  name: kolibri_explore_plugin

  url: https://files.pythonhosted.org/packages/82/00/6c8e5d97b1f3c974d12724f9ba992fddf79a9960d9067d15aac33f4971b6/kolibri_explore_plugin-2.0.14-py2.py3-none-any.whl
  sha256sum: 456f4bd75d5739b54904c3efb8b3b726d5e3d23f9daaf91327e54f963c63c940

- kind: pypi
  name: kolibri_zim_plugin

  url: https://files.pythonhosted.org/packages/18/5b/feb81624b6a0e2c72f29a54e5177520a62400763b85c7ae4f710222cb925/kolibri_zim_plugin-1.3.1-py2.py3-none-any.whl
  sha256sum: 596693d192d349612a5b589a94a3a761679e81a832daa1420c6b264aa88ba075

- kind: github_release
  repo: endlessm/kolibri-explore-plugin
  asset: apps-bundle.zip

  url: https://github.com/endlessm/kolibri-explore-plugin/releases/download/v2.0.14/apps-bundle.zip
  asset_id: '58874911'

config:
  install-commands:
  - mkdir -p %{install-root}/plugins
  - unzip -o -d %{install-root}/plugins kolibri_zim_plugin.zip
  - unzip -o -d %{install-root}/plugins/ kolibri_explore_plugin.zip
  - unzip -o -d %{install-root}/plugins/kolibri_explore_plugin apps-bundle.zip
