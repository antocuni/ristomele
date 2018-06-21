# this is a build script using the p4a's old_toolchain.
# the new one suffers of this bug:
# https://github.com/kivy/kivy/issues/4466

NAME := "RistoMele"
PACKAGE := "eu.antocuni.ristomele"
VERSION := 0.1

space =
space +=
apk := $(subst $(space),,$(NAME))
apk := $(apk)-$(VERSION)# something like "RistoMele-0.2"
DEBUG := bin/$(apk)-debug.apk
UNSIGNED := bin/$(apk)-release-unsigned.apk
UNALIGNED := bin/$(apk)-release-unaligned.apk
RELEASE := bin/$(apk).apk

P4A := /home/antocuni/.virtualenvs/p4a/bin/p4a
ADB := /extra/android/android-sdk-linux_x86/platform-tools/adb
this := $(abspath $(lastword $(MAKEFILE_LIST))) # abspath of the Makefile
ROOT := $(dir $(this))

# ==================
# configure build.py

BUILDFLAGS  = --dir $(ROOT)/launcher
BUILDFLAGS += --package $(PACKAGE)
BUILDFLAGS += --name $(NAME)
BUILDFLAGS += --version $(VERSION)
#BUILDFLAGS += --icon $(ROOT)/play/icon.png
BUILDFLAGS += --permission INTERNET
#BUILDFLAGS += --permission CAMERA
BUILDFLAGS += --orientation portrait
#BUILDFLAGS += --minsdk 13
BUILDFLAGS += --window
#BUILDFLAGS += --launcher # make a kivy launcher instead of a standalone app
BUILDFLAGS += --bootstrap=sdl2
BUILDFLAGS += --requirements=python2,kivy

BASE=/extra/android/
export ANDROIDAPI=19
export ANDROIDSDK=$(BASE)/android-sdk-linux_x86/
export ANDROIDNDK=$(BASE)/android-ndk-r9c/
export ANDROIDNDKVER=r9c

debug:
	@echo [DEBUG] $(DEBUG)
	$(P4A) apk $(BUILDFLAGS)
	@mv *.apk bin

install:
	$(ADB) install -r $(DEBUG)

logcat:
	$(ADB) logcat | grep python


# release:
# # build APK
# 	@echo [BUILD] $(UNSIGNED)
# 	@ cd $(P4A)/dist/default; ./build.py $(BUILDFLAGS) release
# 	@cp $(P4A)/dist/default/$(UNSIGNED) $(ROOT)/bin
# # sign
# 	@echo [JARSIGNER] $(UNALIGNED)
# 	@jarsigner \
# 		-sigalg SHA1withRSA \
# 		-digestalg SHA1 \
# 		-keystore play/mykey.keystore \
# 		-storepass password \
# 		$(UNSIGNED) \
# 		alias_name
# 	@mv $(UNSIGNED) $(UNALIGNED)
# 	@echo
# # zipalign
# 	@echo [ZIPALIGN] $(RELEASE)
# 	@rm -f $(RELEASE)
# 	@zipalign 4 $(UNALIGNED) $(RELEASE)
# 	@rm $(UNALIGNED)


# key: play/mykey.keystore

# play/mykey.keystore:
# 	keytool -genkey -v -keystore play/mykey.keystore -alias alias_name -keyalg RSA -keysize 2048 -validity 10000

