#!/usr/bin/env python3
# Inject eMMC sysupgrade.itb (self-contained FIT) into supergateway_s20-common.
# S20 系列 eMMC + yuzhi U-Boot：原生定义只产 sysupgrade.tar，web failsafe/后台直刷 tar 会 brick。
# 把 sysupgrade.bin 从 tar 直接改成自包含 FIT itb（文件名仍叫 .bin：assembler 的 build.sh 取像
# 只认 *.bin、不认 .itb；FIT 魔数 0xd00dfeed 与扩展名无关，web-failsafe/LuCI 都照常识别）。
# 对齐 asus_rt-ax59u-ubi / tplink_wma301-common 的 eMMC itb 模板。
# 关键: supergateway 的 DEVICE_DTS 在 sub-device 的 $(call ...-common) 之后才赋值, 故 IMAGE recipe
#       里的 $(KDIR)/$(DEVICE_DTS) 必须用双 $(延迟展开), 单 $ 会在 define 解析期展开成空 → image-.dtb。
# 幂等：已注入则跳过。CWD 应为 openwrt/ 源码根。
import sys, os


def main():
    p = "target/linux/mediatek/image/filogic.mk"
    if not os.path.isfile(p):
        print("[inject] !! 找不到 %s (CWD=%s)，请确认 working-directory" % (p, os.getcwd()))
        sys.exit(1)
    s = open(p, encoding="utf-8").read()

    if "\tIMAGE/sysupgrade.bin := append-kernel" in s:
        print("[inject] 已含 s20 eMMC itb(sysupgrade.bin 内容) 注入，跳过（幂等）")
        sys.exit(0)

    block_anchor = "define Device/supergateway_s20-common"
    img_anchor = "IMAGE/sysupgrade.bin := sysupgrade-tar | append-metadata"

    bi = s.find(block_anchor)
    if bi == -1:
        print("[inject] !! 未找到 supergateway_s20-common，请检查 VIKINGYFY 源")
        sys.exit(1)
    ji = s.find(img_anchor, bi)
    if ji == -1:
        print("[inject] !! s20-common 内未找到 sysupgrade.bin(tar) 锚点")
        sys.exit(1)

    inject = (
        "\tIMAGES := sysupgrade.bin\n"
        "\tKERNEL := kernel-bin | lzma\n"
        "\tIMAGE/sysupgrade.bin := append-kernel | fit lzma $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb external-with-rootfs | append-metadata\n"
    )

    s = s[:ji] + inject + s[ji + len(img_anchor):]
    open(p, "w", encoding="utf-8").write(s)

    assert "\tIMAGE/sysupgrade.bin := append-kernel" in s, "s20 itb 注入校验失败"
    print("[inject] supergateway_s20 注入 eMMC sysupgrade.itb(落为 sysupgrade.bin) 成功")


if __name__ == "__main__":
    main()
