/*
 * Copyright (c) 2022 Bohdan Marukhnenko
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

package pages

import (
	"github.com/PaulSonOfLars/gotgbot/v2"
	"github.com/cubicbyte/dteubot/internal/i18n"
)

func CreateAdminPanelPage(lang i18n.Language) (Page, error) {
	page := Page{
		Text: lang.Page.AdminPanel,
		ReplyMarkup: gotgbot.InlineKeyboardMarkup{
			InlineKeyboard: [][]gotgbot.InlineKeyboardButton{
				{{
					Text:         lang.Button.ClearCache,
					CallbackData: "admin.clear_cache",
				}},
				{{
					Text:         lang.Button.ClearLogs,
					CallbackData: "admin.clear_logs",
				}},
				{{
					Text:         lang.Button.GetLogs,
					CallbackData: "admin.get_logs",
				}},
				{{
					Text:         lang.Button.Back,
					CallbackData: "open.menu",
				}},
			},
		},
		ParseMode: "MarkdownV2",
	}

	return page, nil
}
