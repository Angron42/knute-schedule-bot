package commands

import (
	"github.com/cubicbyte/dteubot/internal/dteubot/pages"
	"github.com/cubicbyte/dteubot/internal/dteubot/settings"
	"github.com/cubicbyte/dteubot/internal/dteubot/utils"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func handleCallsCommand(u *tgbotapi.Update) error {
	cManager := utils.GetChatDataManager(u.FromChat().ID)

	page, err := pages.CreateCallSchedulePage(cManager, "open.menu#from=calls")
	if err != nil {
		return err
	}

	_, err = settings.Bot.Send(page.CreateMessage(cManager.ChatId))
	if err != nil {
		return err
	}

	return nil
}
