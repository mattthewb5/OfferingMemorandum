#!/bin/bash
# Revert unified_app.py back to original version after testing

if [ -f unified_app.py.backup ]; then
    cp unified_app.py.backup unified_app.py
    echo "✓ Reverted unified_app.py to original version"
    echo "✓ Testing change removed"
    rm unified_app.py.backup
    echo "✓ Backup file removed"
else
    echo "❌ Backup file not found"
fi
