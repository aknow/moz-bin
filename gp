#!/bin/bash
git format-patch -U8 --no-stat --no-signature $@ | xargs gp2hgp

