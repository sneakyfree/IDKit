# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic:
    - link "Skip to main content" [ref=e2] [cursor=pointer]:
      - /url: "#main-content"
    - link "Skip to navigation" [ref=e3] [cursor=pointer]:
      - /url: "#main-navigation"
  - status [ref=e4]
  - generic [ref=e6]:
    - heading "404" [level=1] [ref=e7]
    - heading "This page could not be found." [level=2] [ref=e9]
  - generic [ref=e11]:
    - img [ref=e12]
    - generic [ref=e14]: You & apos;re offline
    - generic [ref=e15]: Changes will sync when online
  - alert [ref=e16]
```