# owai-ib-builder

编译一个**适配 OWAI（dl.openwrt.ai）源**的 OpenWrt **opkg** ImageBuilder，用于 firmware-assembler 或自建 `make image`。

## 背景
- OpenWrt / ImmortalWrt 25.12 默认 **APK**，而 owai 的包是 **opkg**，格式不互通 → 官方/ImmortalWrt 的 25.12 IB 装不进 owai 的包。
- 本工作流**强制 opkg**，并把生成的 `repositories.conf` 对齐 owai 的五个分流（base / luci / packages / routing / video / kiddin9），同时关掉 `option check_signature`（owai 的包不是我们签的，开着会整盘拒装）。

## 用法
仓库 **Actions → `workflow_dispatch`** 触发，参数见工作流 `inputs`：

| 参数 | 默认 | 说明 |
|------|------|------|
| `target` | `mediatek/filogic` | 格式 `<board>/<subtarget>` |
| `openwrt_branch` | `openwrt-25.12` | openwrt/openwrt 分支 |
| `openwrt_ref` | 空 | 可选精确 commit |
| `use_apk` | `false` | 必须保持 opkg，否则与 owai 不通 |
| `standalone` | `true` | 自带全部包（含 kmod）；关掉则固件缺 kmod |
| `kiddin9_feed` | `true` | owai 那些包就是 op-packages 编出来的 |
| `version_repo` | `https://dl.openwrt.ai/releases/25.12` | 写进 IB 的远端基址 |
| `make_release` | `false` | 是否发 GitHub Release |

产物：ImageBuilder `tar.zst`（自带与自身内核匹配的 kmod），以 **Artifact / Release** 提供。

## 实现要点（为什么 patch make 文件而不是直接写 `.config`）
在 `openwrt-25.12` 分支里，`VERSION_DIST/NUMBER/REPO` 与 `PER_FEED_REPO` 这些 Kconfig 符号已从 `Config-build.in` / `Config-images.in` 消失（GitHub API + jsDelivr 双重实锤），写进 `.config` 会被 Kconfig 直接丢弃。因此本流程直接在 make 文件层对齐 owai：

1. `include/version.mk` — `VERSION_REPO/NUMBER/DIST` 默认值改 owai（→ `%U` 变 owai）
2. `include/feeds.mk` — 重写 `FeedSourcesAppendOPKG` 为硬编码 owai 五分流，删掉 core 行与 kmods 行（owai 无 `targets/` 分流，实测 404）
3. `target/imagebuilder/Makefile` — 删掉无条件 `echo 'option check_signature'`

## 已知未验证项
- 未经实跑；首次运行可能需迭代（尤其 `feeds.mk` 重写的匹配、kiddin9 全量编译耗时，standalone 预计 1.5–2.5h）。
- owai 25.12 分流实测：base/luci/packages/routing/video/kiddin9 = 200；telephony / targets（含 kmods）= 404。
