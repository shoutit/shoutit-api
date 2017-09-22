#!/usr/bin/env bash

# Set BUILD_TAG to $CIRCLE_BUILD_NUM
echo "BUILD_TAG=${CIRCLE_BUILD_NUM}"
echo "export BUILD_TAG=${CIRCLE_BUILD_NUM}" >> $BASH_ENV

# Set BUILD_BRANCH
case "${CIRCLE_TAG:-$CIRCLE_BRANCH}" in
    release-*)
      BUILD_BRANCH=live
    ;;
    stage-*)
      BUILD_BRANCH=${CIRCLE_TAG}
    ;;
    *)
      BUILD_BRANCH=${CIRCLE_BRANCH}
    ;;
esac

echo "BUILD_BRANCH=${BUILD_BRANCH}"
echo "export BUILD_BRANCH=${BUILD_BRANCH}" >> $BASH_ENV
