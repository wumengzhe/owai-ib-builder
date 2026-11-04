#!/usr/bin/env python3
# Inject sysupgrade.itb into supergateway_s20-common (eMMC + yuzhi U-Boot).
# S20 系列 eMMC + yuzhi U-Boot：原生定义只产 sysupgrade.tar，web failsafe/后台直刷 tar 会 brick。
# 注入自包含 FIT (sysupgrade.itb)，对齐 asus_rt-ax59u-ubi eMMC 模板；保留 tar 给 assembler 内部升级。
# 幂等：已注入则跳过。CWD 应为 openwrt/ 源码根。
import sys, os


def main():
    p = "target/linux/mediatek/image/filogic.mk"
    if not os.path.isfile(p):
        print("[inject] !! 找不到 %s (CWD=%s)，请确认 working-directory" % (p, os.getcwd()))
        sys.exit(1)
    s = open(p, encoding="utf-8").read()

    if "\tIMAGE/sysupgrade.itb := append-kernel" in s:
        print("[inject] 已含 sysupgrade.itb，跳过（幂等）")
        sys.exit(0)

    block_anchor = "define Device/supergateway_s20-common"
    img_anchor = "IMAGE/sysupgrade.bin := sysupgrade-tar | append-metadata"

    bi = s.find(block_anchor)
    if bi == -1:
        print("[inject] !! 未找到 supergateway_s20-common，请检查 VIKINGYFY 源")
        sys.exit(1)
    ji = s.find(img_anchor, bi)
    if ji == -1:
        print("[inject] !! s20-common 内未找到 sysupgrade.bin 锚点")
        sys.exit(1)

    inject = (
        "\tIMAGES := sysupgrade.bin sysupgrade.itb\n"
        "\tKERNEL := kernel-bin | lzma\n"
        "\tIMAGE/kernel := kernel-bin | append-dtb | lzma | fit lzma $(KDIR)/image-$(firstword $(DEVICE_DTS)).dtb\n"
        "\tIMAGE/sysupgrade.itb := append-kernel | \\\n"
        "\t\tfit lzma $(KDIR)/image-$(firstword $(DEVICE_DTS)).dtb external-with-rootfs | \\\n"
        "\t\tpad-rootfs | append-metadata\n"
    )

    s = s[:ji] + inject + s[ji:]
    open(p, "w", encoding="utf-8").write(s)

    assert "\tIMAGE/sysupgrade.itb := append-kernel" in s, "itb 注入校验失败"
    print("[inject] supergateway_s20 注入 sysupgrade.itb 成功")


if __name__ == "__main__":
    main()
