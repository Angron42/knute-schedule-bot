package dteubot

import (
	"github.com/cubicbyte/dteubot/internal/data"
	"github.com/cubicbyte/dteubot/internal/dteubot/pages"
	"github.com/cubicbyte/dteubot/internal/dteubot/settings"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func handleLanguageCommand(u *tgbotapi.Update) error {
	cManager := data.ChatDataManager{ChatId: u.FromChat().ID}

	page, err := pages.CreateLanguageSelectionPage(&cManager, "open.menu#from=language")
	if err != nil {
		return err
	}

	_, err = settings.Bot.Send(page.CreateMessage(cManager.ChatId))
	if err != nil {
		return err
	}

	return nil
}
