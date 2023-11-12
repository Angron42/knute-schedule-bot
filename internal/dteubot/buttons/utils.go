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

package buttons

import (
	"github.com/cubicbyte/dteubot/internal/dteubot/pages"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

// editPage edits the message with the given page.
func editPage(page *pages.Page, err error, u *tgbotapi.Update, bot *tgbotapi.BotAPI) error {
	if err != nil {
		return err
	}

	conf := page.CreateEditMessageOpts(u.CallbackQuery.Message.Chat.ID, u.CallbackQuery.Message.MessageID)
	_, err = bot.Send(conf)
	if err != nil {
		return err
	}

	return nil
}
