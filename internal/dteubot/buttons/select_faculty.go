package buttons

import (
	"errors"
	"github.com/cubicbyte/dteubot/internal/dteubot/pages"
	"github.com/cubicbyte/dteubot/internal/dteubot/settings"
	"github.com/cubicbyte/dteubot/internal/dteubot/utils"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"strconv"
)

func HandleSelectFacultyButton(u *tgbotapi.Update) error {
	// Get facultyId and structureId from button data
	button := utils.ParseButtonData(u.CallbackQuery.Data)

	facultyId, ok := button.Params["facultyId"]
	if !ok {
		return errors.New("no facultyId in button data")
	}
	structureId, ok := button.Params["structureId"]
	if !ok {
		return errors.New("no structureId in button data")
	}

	facId, err := strconv.Atoi(facultyId)
	if err != nil {
		return err
	}
	structId, err := strconv.Atoi(structureId)
	if err != nil {
		return err
	}

	// Create page
	cManager := utils.GetChatDataManager(u.FromChat().ID)
	page, err := pages.CreateCoursesListPage(cManager, facId, structId)
	if err != nil {
		return err
	}

	_, err = settings.Bot.Send(EditMessageRequest(page, u.CallbackQuery))
	if err != nil {
		return err
	}

	return nil
}
