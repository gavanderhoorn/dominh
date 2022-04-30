# flake8: noqa

# Copyright (c) 2022, G.A. vd. Hoorn
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# author: G.A. vd. Hoorn

# Constants defined in klevkeys.kl, V770-1

from enum import IntEnum


class KeyCode(IntEnum):
    # Undefined key
    KY_UNDEF        = 255

    # Shift key
    KY_SHIFT        = 0

    # E-STOP, Enable, Deadman
    TPI_ESTOP       = 250
    TPI_ENABLE      = 249
    TPI_R_DMAN      = 248
    TPI_L_DMAN      = 247

    # Arrow keys
    KY_UP_ARW       = 212
    KY_DN_ARW       = 213
    KY_RT_ARW       = 208
    KY_LF_ARW       = 209

    # Operator panel key requests--not to be used
    # for KAREL SOPIN/UOPIN/OPIN requests (use
    # CMS_KL:KLIOSOP.KL, KLIOUOP.KL)
    OP_RESET        = 165
    OP_SOP_START    = 166
    OP_UOP_START    = 167
    OP_UOP_CSTOP    = 168
    OP_UOP_HOME     = 169

    # Special shell command keys (to TPMM)
    M_RECOVER_C     = 164
    M_PRODSCRN_C    = 242
    SHELL_FWD_C     = 160
    SHELL_BWD_C     = 161

    # Term_key codes for non-key terminations
    TK_BUFF_FULL    = 255
    TK_NO_WINDOW    = 254
    TK_NO_KB        = 253
    # tk_cancel is defined as ky_cancel below
    TK_TIMEOUT      = 251
    TK_UI_LOADED    = 226

    # **********************************************   TP only keys
    # Hard keys (shifted or unshifted )
    TPI_SELECT   = 143
    TPI_MENUS    = 144
    TPI_EDIT     = 145
    TPI_DATA     = 146
    TPI_FUNCTION = 147

    # Misc. keys
    TPI_ITEM     = 148
    TPI_PCT_UP   = 149
    TPI_PCT_DN   = 150
    TPI_HOLD     = 151
    TPI_STEP     = 152
    TPI_RESET    = 153
    TPI_GROUP    = 28

    # Shifted misc keys
    KY_ITEM_S    = 154
    TPI_PCT_UP_S = 155
    TPI_PCT_DN_S = 156
    TPI_STEP_S   = 157
    TPI_HOLD_S   = 158
    TPI_RESET_S  = 159

    # Key codes for non-hardkey menus
    TPI_M_SYSTEM = 151
    TPI_M_STAT   = 154
    TPI_M_ALARM  = 162
    TPI_M_VISION = 163
    TPI_M_SWG_EQ = 243
    TPI_M_MAC_MF = 244
    TPI_M_USER2  = 245 # USER2 menu (used by form and table managers)

    # Motion related keys
    TPI_FWD      = 185
    TPI_BWD      = 186
    TPI_COORD    = 187
    TPI_X_PLS    = 188
    TPI_Y_PLS    = 189
    TPI_Z_PLS    = 190
    TPI_W_PLS    = 191
    TPI_P_PLS    = 192
    TPI_R_PLS    = 193
    TPI_X_MNS    = 194
    TPI_Y_MNS    = 195
    TPI_Z_MNS    = 196
    TPI_W_MNS    = 197
    TPI_P_MNS    = 198
    TPI_R_MNS    = 199

    # Shifted motion related keys
    TPI_FWD_S    = 200
    TPI_BWD_S    = 201
    TPI_COORD_S  = 202
    TPI_X_PLS_S  = 214
    TPI_Y_PLS_S  = 215
    TPI_Z_PLS_S  = 216
    TPI_W_PLS_S  = 217
    TPI_P_PLS_S  = 218
    TPI_R_PLS_S  = 219
    TPI_X_MNS_S  = 220
    TPI_Y_MNS_S  = 221
    TPI_Z_MNS_S  = 222
    TPI_W_MNS_S  = 223
    TPI_P_MNS_S  = 224
    TPI_R_MNS_S  = 225

    TPI_CHG_EQ_C = 228

    # **********************************************   TP & CRT Shared keys

    # Keypad keys (shifted or unshifted)
    KY_ENTER     = 13
    KY_BCKSPACE  =  8
    KY_COMMA     = 44
    KY_MINUS     = 45
    KY_DOT       = 46
    KY_ZERO      = 48
    KY_ONE       = 49
    KY_TWO       = 50
    KY_THREE     = 51
    KY_FOUR      = 52
    KY_FIVE      = 53
    KY_SIX       = 54
    KY_SEVEN     = 55
    KY_EIGHT     = 56
    KY_NINE      = 57

    # /* top row keys */
    KY_PREV      = 128
    KY_F1        = 129
    KY_F2        = 131
    KY_F3        = 132
    KY_F4        = 133
    KY_F5        = 134
    KY_NEXT      = 135

    # Shifted top row keys
    KY_PREV_S    = 136
    KY_F1_S      = 137
    KY_F2_S      = 138
    KY_F3_S      = 139
    KY_F4_S      = 140
    KY_F5_S      = 141
    KY_NEXT_S    = 142

    # Key codes for special actions
    KY_DISP_UPDT   = 170
    KY_REISSUE     = 171
    KY_CANCEL      = 252
    KY_NEW_MENU    = 0
    KY_WARN_REQ    = 172

    # Shifted arrow keys
    KY_UP_ARW_S    = 204
    KY_DN_ARW_S    = 205
    KY_RT_ARW_S    = 206
    KY_LF_ARW_S    = 207

    # /* user function keys */
    KY_UF_1        = 173
    KY_UF_2        = 174
    KY_UF_3        = 175
    KY_UF_4        = 176
    KY_UF_5        = 177
    KY_UF_6        = 178
    KY_UF_7        = 210

    # shifted user function keys
    KY_UF_1_S      = 179
    KY_UF_2_S      = 180
    KY_UF_3_S      = 181
    KY_UF_4_S      = 182
    KY_UF_5_S      = 183
    KY_UF_6_S      = 184
    KY_UF_7_S      = 211

    # function keys
    KY_F6          = 194
    KY_F7          = 195
    KY_F8          = 196
    KY_F9          = 197
    KY_F10         = 198
    KY_HELP        = 203


    # ************************************* VT220 only keys */
    # F1 - F10 already defined in TP keys ky_f1 - ky_f10
    KY_F11       = 199
    KY_F12       = 200
    KY_F13       = 201
    KY_F14       = 202
    KY_DISP_S    = 227
    KY_DIAG      = 239
    KY_DISP      = 240
    KY_DO        = 241
    KY_F17       = 238
    KY_F18       = 235
    KY_F19       = 236
    KY_F20       = 237

    # Editing keys
    KY_FIND      = 229
    KY_INSERT    = 230
    KY_REMOVE    = 231
    KY_SELECT    = 232
    KY_PRV_SCR   = 233
    KY_NXT_SCR   = 234

    # PF keys
    KY_PF1       = 225
    KY_PF2       = 226
    KY_PF3       = 227
    KY_PF4       = 240

    # Numeric keypad keys
    KY_NKP_0     = 176
    KY_NKP_1     = 177
    KY_NKP_2     = 178
    KY_NKP_3     = 179
    KY_NKP_4     = 180
    KY_NKP_5     = 181
    KY_NKP_6     = 182
    KY_NKP_7     = 183
    KY_NKP_8     = 184
    KY_NKP_9     = 185
    KY_NKP_MNS   = 186
    KY_NKP_CMA   = 187
    KY_NKP_DOT   = 188
    KY_NKP_NTR   = 239

    # Misc keys
    KY_CTL_U     =  21
    KY_CTL_W     =  23
    KY_DELETE    = 127

    # T-X TP hardkey
    KY_FAST      = 130  # no longer supported
    KY_SLOW      = 246  # no longer supported

    # Double byte character input for iPendant and CRT
    KANJI_IN_C   = 130
    KANJI_OUT_C  = 246

    # Extended key code definitions
    EXTEND_KEY_C = 1

    # keys sent only to iPendant
    IP_BCK_C     = 4097  # 0x1001 iPendant BACK key */
    IP_FWD_C     = 8193  # 0x2001 iPendant FOWARD key */
    IP_FRAME_BCK = 12289 # 0x3001 iPendant FRAME BACK key */
    IP_FRAME_FWD = 16385 # 0x4001 iPendant FRAME FORW key */
