# 📝 Library Changelog:

## 🆕 Version 2.0.23
### 📦 apodiktum_library:
#### Utils:
- added | `raw_text` to optionally support custom emojis, check docstring
- added | `remove_html` check docstring
- removed | `rem_customemoji_html`

## 🆕 Version 2.0.22
### 📦 apodiktum_library:
#### General:
- `lib_version` now stored temporarily

## 🆕 Version 2.0.21
### 📦 apodiktum_library:
#### Utils:
- rework | check `doc_string`

#### Watcher_q:
- rework |  added `except exception` to `__queue_method_handler`

## 🆕 Version 2.0.20
### 📦 apodiktum_library:
#### Watcher_q:
- rework | now also supports `any` method and also multiple per module

## 🆕 Version 2.0.19
### 📦 apodiktum_library:
#### General:
- fix | `watcher_q` now successfully cancel tasks
- rework | internal stuff

## 🆕 Version 2.0.18
### 📦 apodiktum_library:
#### General:
- add | `watcher_q` as class, which processes messages one after the other

## 🆕 Version 2.0.17
### 📦 apodiktum_library:
#### Utils:
- add | `rem_customemoji_html` to remove `<emoji document_id="xyz"></emoji>`

## 🆕 Version 2.0.16
### 📦 apodiktum_library:
#### General:
 scope: hikka_min 1.3.3
 
#### Utils:
- removed | `get_fullchannel`
- removed | `get_perms`

## 🆕 Version 2.0.15
### 📦 apodiktum_library:
#### General:
- fix config defaulting after update

## 🆕 Version 2.0.14
### 📦 apodiktum_library:
#### General:
- set `version` of the current loaded version into db

## 🆕 Version 2.0.13
### 📦 apodiktum_library:
#### Utils:
- add | `get_fullchannel` to get cached `GetFullChannelRequest`

## 🆕 Version 2.0.12
### 📦 apodiktum_library:
#### Utils:
- add | `get_perms` to get cached `get_permissions`
- change | `delete_message` now supports `deltimer`

## 🆕 Version 2.0.11
### 📦 apodiktum_library:
#### Utils:
- change | `is_member` now returns `perms` if `True`

## 🆕 Version 2.0.10
### 📦 apodiktum_library:
#### Utils:
- add | `get_file_from_url`
- add | `get_first_msg`

## 🆕 Version 2.0.9
### 📦 apodiktum_library:
#### General:
- reworked stats sender
#### Utils:
- added | `unmute`
- added | `unban`
- added | `asset_channel`

## 🆕 Version 2.0.8
### 📦 apodiktum_library:
#### General:
- refactor for Hikka 1.3.0

## 🆕 Version 2.0.7
### 📦 apodiktum_library:
#### Utils:
- changed | `check_inlinebot`
- changed | `invite_bot`
- changed | `promote_bot`
- fixed | `is_member`

## 🆕 Version 2.0.6
### 📦 apodiktum_library:
#### General:
- changed copyright banner

## 🆕 Version 2.0.5
### 📦 apodiktum_library:
#### General:
- changed copyright banner

## 🆕 Version 2.0.4
### 📦 apodiktum_library:
#### General:
- black formatting

## 🆕 Version 2.0.3
### 📦 apodiktum_library:
#### Utils:
- added | `check_inlinebot`
- added | `promote_bot`
- added | `mute`
- added | `kick`
- added | `ban`
- added | `delete_message`
- fixed | `get_tag`
- fixed | `validate_boolean`

## 🆕 Version 2.0.2
### 📦 apodiktum_library:
#### General:
- Ensure pushing anonymous stats

## 🆕 Version 2.0.1
### 📦 apodiktum_library:
#### Utils:
- fixed get_user_id for peer_id._channel_id

## 🆕 Version 2.0.0
### 📦 apodiktum_library:
#### General:
- Library now supports scope for requirments, not need to add unnecessary imports into the module
