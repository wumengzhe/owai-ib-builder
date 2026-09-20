# owai-ib-builder

编译一个**适配 OWAI（dl.openwrt.ai）源**的 OpenWrt **opkg** ImageBuilder，用于 firmware-assembler 或自建 `make image`。

## 背景
- OpenWrt / ImmortalWrt 25.12 默认 **APK**，而 owai 的包是 **opkg**，格式不互通 → 官方/ImmortalWrt 的 25.12 IB 装不进 owai 的包。本工作流**强制 opkg**。
- **owai 没有可用的远程 kmod**（无 `targets/` 分流，实测 404）。固件要能跑（WiFi / 内核模块）必须有与自身内核匹配的 kmod。因此本 IB 采用 **`CONFIG_IB_STANDALONE=y`**：把全部包（含 kmod）**本地捆绑**进 tarball，`repositories.conf` 只保留本地源 `src imagebuilder file:packages`。
- **"适配 OWAI 源"= 同代同源**：IB 从 `openwrt-25.12` 编出（与 owai 的 25.12 包同代），包格式、ABI、vermagic 一致。当用户态包需要增量更新时，下游 firmware-assembler 通过 `OWAI_BASE_URL` 把 owai 远程源**注入**到构建中；kmod 始终走本地捆绑（owai 无 kmod）。

## 用法
仓库 **Actions → `workflow_dispatch`** 触发（push 到 `main` 且改动 `.github/workflows/**` 也会自动跑）。参数见工作流 `inputs`：

| 参数 | 默认 | 说明 |
|------|------|------|
| `target` | `mediatek/filogic` | 格式 `<board>/<subtarget>` |
| `openwrt_branch` | `openwrt-25.12` | openwrt/openwrt 分支 |
| `openwrt_ref` | 空 | 可选精确 commit |
| `use_apk` | `false` | 必须保持 opkg，否则与 owai 不通 |
| `standalone` | `true` | 自带全部包（含 kmod）；关掉则固件缺 kmod，对 owai 不可用 |
| `kiddin9_feed` | `true` | owai 那些包就是 op-packages 编出来的 |
| `version_repo` | `https://dl.openwrt.ai/releases/25.12` | version.mk 里的远端基址（仅影响 %U 展示，不影响捆绑包） |
| `make_release` | `false` | 是否发 GitHub Release |

产物：ImageBuilder `tar.zst`（自带与自身内核匹配的 kmod），以 **Artifact** 提供。

## 实现要点
- **`.config` 必须显式写 `CONFIG_IB=y`**：`config IB` 的默认值是 `BUILDBOT`（CI 上未设→n），而 `IB_STANDALONE depends on IB`。只写 `CONFIG_IB_STANDALONE=y` 会被 `make defconfig` 因依赖不满足**静默丢弃**（无任何报错），IB 退化成非 standalone → 无 kmod。
- **强制 opkg**：`use_apk=false` → `# CONFIG_USE_APK is not set`。
- **去掉签名校验**：`target/imagebuilder/Makefile` 里删掉无条件的 `echo 'option check_signature'`（owai 的包不是我们签的，开着会整盘拒装）。
- **构建顺序**：OpenWrt top-level 直接拿 `package/install` / `target/imagebuilder/compile` 当 goal 会跳过编译、且宿主 opkg 未构建（25.12 无 `tools/opkg`，宿主 opkg 来自 `package/system/opkg` 的 HOST_BUILD）。必须显式逐级：
  `tools/install → toolchain/install → target/compile → package/compile → package/install → target/imagebuilder/compile`。

## 已验证（2026-09-20，commit 7d2af33 之后）
- 构建成功产出 `openwrt-imagebuilder-mediatek-filogic.Linux-x86_64.tar.zst`，内含 **66 个 kmod** + 全部 userland ipk（平铺在 `packages/`）。
- 全量 standalone 编译耗时约 **2–3h**（GitHub Actions ubuntu-22.04）。
- owai 25.12 分流实测：base/luci/packages/routing/video/kiddin9 = 200；telephony / targets（含 kmods）= 404。
