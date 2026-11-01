# Touch Review Cards

Updated: 2026-11-01T11:58:16

| id | label | click | roi | expected_next | note |
| --- | --- | --- | --- | --- | --- |
| `20261101-115816-startupworldloadingbar` | StartupWorldLoadingBar | `[1207, 682]` | `[16, 660, 1236, 48]` | StartUpGameWait | 大世界加载读条，非更新下载条。基准 1280x720。有则禁止 PadWatch。点击点是个数字，变成100时读取完毕，或者数字消失读取完毕 |
| `20261101-115006-startuploadingbar` | StartupLoadingBar | `[136, 661]` | `[60, 628, 1168, 57]` | StartUpGameWait | 有进度条则 DoNothing 回等待，不进 PadWatch。基准 1280x720。 |
| `20261101-113824-solaguidebookopened` | SolaGuidebookOpened | `[50, 217]` | `[9, 187, 78, 61]` | GuidebookTacetTab | 成功验证节点：DoNothing。基准 1280x720。 |
| `20261101-113712-solaguidebookextra` | SolaGuidebookExtra | `[51, 214]` | `[25, 193, 53, 49]` | GuidebookTacetTab | 手柄模式索拉指南额外操作。基准 1280x720。 |
| `20261101-113017-startuppadready` | StartupPadReady | `[37, 682]` | `[18, 667, 74, 32]` |  | 同一张手柄态大世界图。基准 1280x720。识别用。上一版 RT 29x25 太小易飘。 |
| `20261101-112446-startuppadready` | StartupPadReady | `[1223, 651]` | `[1208, 639, 29, 25]` |  | 基准 1280x720。识别用。 |
| `20261101-111149-solaguidebooktile` | SolaGuidebookTile | `[634, 499]` | `[589, 474, 87, 118]` | GuidebookTacetTab | 第三行最左。勿点活动/唤取/成就。基准 1280x720。 |
| `20261101-110736-openguidebook` | OpenGuidebook | `[1221, 35]` | `[1207, 28, 27, 21]` | SolaGuidebookTile | 当前流水线误用过 1225,28（易进系统菜单）和 1198,38。请按你实测能打开 Terminal 的点标注。基准 1280x720。 |
| `20261101-110628-solaguidebooktile` | SolaGuidebookTile | `[1113, 33]` | `[1095, 16, 37, 39]` | GuidebookTacetTab | 禁止点「活跃行迹 / 周度游历」。坐标基准 1280×720。 |
| `20261031-204819-tacetgoindex3` | TacetGoIndex3 | `[1150, 439]` | `[1071, 420, 156, 49]` | TacetStartChallenge | 同列表图。Index1/2 已入库。行距约 103px（235→338）。 |
| `20261031-204735-tacetgoindex2` | TacetGoIndex2 | `[1148, 338]` | `[1070, 321, 157, 38]` | TacetStartChallenge | 同列表图续标第2行。Index1 已入库 20261031-204447。 |
| `20261031-204447-tacetgoindex1` | TacetGoIndex1 | `[1139, 235]` | `[1067, 209, 160, 54]` | TacetStartChallenge | 多副本选行。ok-ww 配置序号1起；首屏约4行。现网若在登录页，用本历史列表图即可。 |
| `20261031-203550-tacetstaminaexhausted` | TacetStaminaExhausted | `[969, 230]` | `[932, 212, 66, 47]` | ExploreHUD | 60与120数字皆红=体力不足。关弹窗后结束无音区并跳过后续耗体任务。 |
| `20261031-203103-tacetexit` | TacetExit | `[473, 612]` | `[360, 579, 223, 68]` | ExploreHUD | 从已导出结算图复制，专标退出。 |
| `20261031-202836-tacetclaimstamina` | TacetClaimStamina | `[443, 457]` | `[311, 414, 245, 73]` | TacetContinue | 确认：本图即双倍不可用时的回退态（60白/120红）。 |
| `20261031-202743-tacetcontinue` | TacetContinue | `[805, 614]` | `[694, 585, 236, 62]` | InTacetCombat | 结算页。续刷点重新挑战；体力不足/收工点退出副本（下一卡 TacetExit）。 |
| `20261031-202345-tacetclaimstaminadouble` | TacetClaimStaminaDouble | `[838, 451]` | `[718, 421, 245, 64]` | TacetContinue | 120白字=可领。流水线优先匹配本节点，失败再回退单倍。 |
| `manual-disconnect-confirm` | DisconnectConfirm | `[790, 455]` | `[720, 431, 140, 48]` |  | from user shot; Click 确认 only — root cause is env |
| `20261031-201111-tacetchallengecomplete` | TacetChallengeComplete | `[639, 196]` | `[538, 172, 193, 51]` | TacetClaimReward | 纯提示、无点击。战斗完成标志 → 下一步找领取奖励。 |
| `20261031-200221-tacetclaimreward` | TacetClaimReward | `[886, 308]` | `[785, 224, 372, 176]` | TacetClaimStamina | 挑战达成跳过。当前为宝藏旁领取奖励提示（对齐 ok-ww pick_f）。 |
| `20261031-194638-intacetcombat` | InTacetCombat | `[182, 212]` | `[26, 196, 313, 33]` | TacetClear or TacetSettle | ADB mumuscreen001。进本后战斗界面；用于判断已在无音区战斗中。 |
| `20261031-194335-tacetstartchallenge` | TacetStartChallenge | `[1094, 661]` | `[816, 520, 422, 181]` | InTacetCombat or Loading | ADB mumuscreen001。点「直接挑战」后进入的编队页；确认进本按钮是「开启挑战」。 |
| `20261031-194119-tacetgobutton` | TacetGoButton | `[1148, 237]` | `[1092, 224, 111, 28]` | TacetChallengeConfirm or InWorldNearTacet | ADB mumuscreen001 实截 1280x720（桥接 192.168.1.50:5555）。文案是「直接挑战」不是「前往」。 |
| `20261031-192736-guidebooktacettab` | GuidebookTacetTab | `[183, 531]` | `[127, 495, 180, 77]` | TacetGoButton | 来源：你提供的窗口截图，已裁掉 MuMu 标题栏并缩到 1280x720。ADB screencap 在安卓15鸣潮上会截到桌面，暂用手动截图。 |
| `20261031-182324-openguidebook` | OpenGuidebook | `[1198, 38]` | `[833, 0, 440, 96]` | GuidebookMain | 安卓用顶部图标代替 PC F2。当前任务栏有「清理聚落中的残象」，与后续聚落任务相关，本次先忽略。 |
| `20261031-181158-openguidebook` | OpenGuidebook | `[1196, 42]` | `[840, 3, 439, 135]` | GuidebookMain or BossBookTabs | 安卓用顶部图标代替 PC 的 F2。无音区在手册左侧分类（ok-ww 点相对坐标约 x=0.24 y=0.73）。 |
| `20261031-173521-explorehud` | ExploreHUD | `[127, 82]` | `[56, 30, 144, 122]` | 地图 | 场景识别节点。稳定特征：左上角小地图。右侧角色头像、技能键先不要标。 |
| `20261031-173027-titleclickconnect` | TitleClickConnect | `[638, 669]` | `[526, 627, 228, 90]` | 进入游戏加载界面 | 只标底部主入口。右侧退出/公告/工具/账号/扫码/设置本次都不要标。 |
| `20261031-172457-titleclickconnect` | TitleClickConnect | `[640, 672]` | `[590, 652, 100, 41]` | 进入登录/选服/公告关闭后，或出现进入游戏相关界面 | 标题页底部「点击连接」。右侧还有退出/公告/工具/账号/扫码/设置，本卡只标主入口。 |
