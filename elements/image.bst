# TODO: Build the img.gz with the software and content

kind: manual

build-depends:
- base.bst

depends:
 - software.bst
 - content.bst

config:
  install-commands:
  - echo "Building image"
