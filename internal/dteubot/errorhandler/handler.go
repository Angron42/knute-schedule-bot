package errorhandler

import (
	"errors"
	"fmt"
	"github.com/cubicbyte/dteubot/internal/dteubot/buttons"
	"github.com/cubicbyte/dteubot/internal/dteubot/pages"
	"github.com/cubicbyte/dteubot/internal/dteubot/settings"
	"github.com/cubicbyte/dteubot/internal/dteubot/utils"
	"github.com/cubicbyte/dteubot/pkg/api"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"github.com/op/go-logging"
	"net/http"
	"net/url"
	"os"
)

var log = logging.MustGetLogger("ErrorHandler")

func HandleError(err error, update tgbotapi.Update) {
	var urlError *url.Error
	var httpApiError *api.HTTPApiError

	switch {
	case errors.As(err, &urlError):
		// Can't make request to the university API

		chat := update.FromChat()
		if chat == nil {
			// Api error with no chat
			log.Errorf("Api request error with no chat: %s", err)
			SendErrorToTelegram(err)
			break
		}

		cm := utils.GetChatDataManager(chat.ID)
		page, err := pages.CreateApiUnavailablePage(cm)
		if err != nil {
			log.Errorf("Error creating api unavailable page: %s", err)
			SendErrorToTelegram(err)
			break
		}

		if update.CallbackQuery != nil {
			_, err = settings.Bot.Send(buttons.EditMessageRequest(page, update.CallbackQuery))
		} else {
			_, err = settings.Bot.Send(page.CreateMessage(cm.ChatId))
		}

		if err != nil {
			log.Errorf("Error sending api unavailable page: %s", err)
			SendErrorToTelegram(err)
		}
	case errors.As(err, &httpApiError):
		// Non-200 api status code

		chat := update.FromChat()
		if chat == nil {
			// Api error with no chat
			log.Errorf("Api error with no chat: %s", err)
			SendErrorToTelegram(err)
			break
		}

		log.Warningf("Api %d error: %s", err.(*api.HTTPApiError).Code, err.(*api.HTTPApiError).Body)

		cm := utils.GetChatDataManager(chat.ID)

		var page *pages.Page
		var pageErr error

		switch err.(*api.HTTPApiError).Code {
		case http.StatusUnauthorized:
			page, pageErr = pages.CreateForbiddenPage(cm, "open.menu#from=unauthorized")

		case http.StatusInternalServerError:
			page, pageErr = pages.CreateApiUnavailablePage(cm)

		case http.StatusForbidden:
			page, pageErr = pages.CreateForbiddenPage(cm, "open.menu#from=forbidden")

		case http.StatusUnprocessableEntity:
			// Request body is invalid: incorrect group id, etc
			for _, field := range err.(*api.HTTPApiError).Err.(*api.ValidationError).Fields {
				switch field.Field {
				case "groupId":
					page, pageErr = pages.CreateInvalidGroupPage(cm)
				default:
					// Unknown field
					page, pageErr = pages.CreateErrorPage(cm)
					log.Errorf("Unknown validation error field: %s", field.Field)
					SendErrorToTelegram(err)
				}
			}
			if page == nil {
				// No fields in ValidationError
				page, pageErr = pages.CreateErrorPage(cm)
				log.Errorf("No fields in ValidationError: %s", err)
				SendErrorToTelegram(err)
			}

		default:
			// Unknown error
			page, pageErr = pages.CreateErrorPage(cm)

			log.Errorf("Unknown API http status code %d: %s", err.(*api.HTTPApiError).Code, err.(*api.HTTPApiError).Body)
			SendErrorToTelegram(err)
		}

		if pageErr != nil {
			log.Errorf("Error creating HTTPApiError page: %s", pageErr)
			SendErrorToTelegram(pageErr)
			break
		}

		if update.CallbackQuery != nil {
			_, err = settings.Bot.Send(buttons.EditMessageRequest(page, update.CallbackQuery))
		} else {
			_, err = settings.Bot.Send(page.CreateMessage(cm.ChatId))
		}

		if err != nil {
			log.Errorf("Error sending HTTPApiError page: %s", err)
			SendErrorToTelegram(err)
		}

	default:
		// Unknown error
		log.Errorf("Unknown error: %s", err)
		chat := update.FromChat()

		if chat == nil {
			// Unknown error with no chat
			log.Errorf("Unknown error with no chat: %s", err)
			SendErrorToTelegram(err)
			break
		}

		cm := utils.GetChatDataManager(chat.ID)
		page, err := pages.CreateErrorPage(cm)
		if err != nil {
			log.Errorf("Error creating error page: %s", err)
			SendErrorToTelegram(err)
			break
		}

		if update.CallbackQuery != nil {
			_, err = settings.Bot.Send(buttons.EditMessageRequest(page, update.CallbackQuery))
		} else {
			_, err = settings.Bot.Send(page.CreateMessage(cm.ChatId))
		}

		if err != nil {
			log.Errorf("Error sending error page: %s", err)
			SendErrorToTelegram(err)
			break
		}

		SendErrorToTelegram(err)
	}
}

func SendErrorToTelegram(err error) {
	chatId := os.Getenv("LOG_CHAT_ID")
	if chatId == "" {
		return
	}

	str := fmt.Sprintf("Error %T: %s", err, err)

	// Send error to Telegram
	_, err2 := settings.Bot.Send(tgbotapi.NewMessageToChannel(chatId, str))
	if err2 != nil {
		// Nothing we can do here, just log the error
		log.Errorf("Error sending error to Telegram: %s", err)
	}
}
