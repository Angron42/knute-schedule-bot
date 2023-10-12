package notifier

import (
	_ "embed"
	"github.com/cubicbyte/dteubot/internal/data"
	"github.com/cubicbyte/dteubot/internal/i18n"
	api2 "github.com/cubicbyte/dteubot/pkg/api"
	"github.com/cubicbyte/dteubot/pkg/api/cachedapi"
	"github.com/go-co-op/gocron"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"github.com/op/go-logging"
	"github.com/sirkon/go-format/v2"
	"strings"
	"time"
)

var Location = "Europe/Kiev"

var log = logging.MustGetLogger("Notifier")

var (
	//go:embed sql/get_chats_15m.sql
	getChats15mQuery string
	//go:embed sql/get_chats_1m.sql
	getChats1mQuery string
)

var (
	db        *data.Database
	api       *cachedapi.CachedApi
	bot       *tgbotapi.BotAPI
	langs     map[string]i18n.Language
	calls     []api2.CallSchedule
	location  *time.Location
	Scheduler *gocron.Scheduler
)

type chatInfo struct {
	ChatId   int64  `db:"chat_id"`
	GroupId  int    `db:"group_id"`
	LangCode string `db:"lang_code"`
}

// Setup initializes notifier and starts cron Scheduler
func Setup(db2 *data.Database, api3 *cachedapi.CachedApi, bot2 *tgbotapi.BotAPI, langs2 map[string]i18n.Language) error {
	log.Info("Setting up notifier")

	db = db2
	api = api3
	bot = bot2
	langs = langs2

	// Setup cron Scheduler
	var err error
	location, err = time.LoadLocation(Location)
	if err != nil {
		return err
	}
	Scheduler = gocron.NewScheduler(location)

	// Get calls
	calls, err = api.GetCallSchedule()
	if err != nil {
		return err
	}

	// Format calls to cron format
	// Call time = "08:20", then cron time += "08:05;08:19;"
	cronTime15m := ""
	cronTime1m := ""
	for _, call := range calls {
		// Parse call start time
		timeStart, err := time.Parse("15:04", call.TimeStart)
		if err != nil {
			return err
		}

		// 15 minutes
		cronTime15m += timeStart.Add(-15*time.Minute).Format("15:04") + ";"

		// 1 minute
		cronTime1m += timeStart.Add(-1*time.Minute).Format("15:04") + ";"
	}
	// Remove last semicolon
	cronTime15m = cronTime15m[:len(cronTime15m)-1]
	cronTime1m = cronTime1m[:len(cronTime1m)-1]

	// Add cron jobs
	_, err = Scheduler.Every(1).Day().At(cronTime15m).Do(SendNotifications, "15m")
	if err != nil {
		panic(err)
	}
	_, err = Scheduler.Every(1).Day().At(cronTime1m).Do(SendNotifications, "1m")
	if err != nil {
		panic(err)
	}

	return nil
}

// SendNotifications sends notifications to chats that subscribed to notifications
func SendNotifications(time2 string) error {
	// Get chats with notifications enabled
	chats, err := GetSubscribedChats("15m")
	if err != nil {
		return err
	}

	// Get current time
	curTime := time.Now().In(location)

	// Send notifications
	for _, chat := range chats {
		// Get group schedule
		schedule, err := api.GetGroupScheduleDay(chat.GroupId, curTime.Format("2006-01-02"))
		if err != nil {
			log.Warningf("Error getting group schedule day for chat %d: %s", chat.ChatId, err)
			continue
		}

		// Check if group have classes
		haveClasses, err := IsGroupHaveClasses(schedule, curTime)
		if err != nil {
			log.Warningf("Error checking if group have classes for chat %d: %s", chat.ChatId, err)
			continue
		}

		if haveClasses {
			// Send notification to chat
			err = SendNotification(chat.ChatId, chat.LangCode, schedule, time2)
			if err != nil {
				log.Warningf("Error sending notification to chat %d: %s", chat.ChatId, err)
				continue
			}
		}
	}

	return nil
}

// SendNotification sends notification to chat
func SendNotification(chatId int64, langCode string, schedule *api2.TimeTableDate, time string) error {
	// Get chat language
	lang, ok := langs[langCode]
	if !ok {
		return &i18n.LanguageNotFoundError{LangCode: langCode}
	}

	// Create page schedule section
	section := ""
	strFormat := "`$lesson\\)` *$name*`[$type]`\n"
	for _, lesson := range schedule.Lessons {
		for _, period := range lesson.Periods {
			section += format.Formatm(strFormat, format.Values{
				"lesson": lesson.Number,
				"name":   period.DisciplineShortName,
				"type":   period.TypeStr,
			})
		}
	}

	// Create page text
	pageText := format.Formatm(lang.Page.ClassesNotification, format.Values{
		"remaining": time,
		"schedule":  section,
	})

	// Create buttons
	replyMarkup := tgbotapi.NewInlineKeyboardMarkup(
		tgbotapi.NewInlineKeyboardRow(
			tgbotapi.NewInlineKeyboardButtonData(lang.Button.OpenSchedule, "open.schedule.day#from=notification&date="+schedule.Date),
			tgbotapi.NewInlineKeyboardButtonData(lang.Button.Settings, "open.settings#from=notification"),
		),
	)

	// Send message
	msg := tgbotapi.NewMessage(chatId, pageText)
	msg.ParseMode = tgbotapi.ModeMarkdownV2
	msg.ReplyMarkup = replyMarkup

	_, err := bot.Send(msg)
	if err != nil {
		return err
	}

	return nil
}

// GetSubscribedChats returns chats that subscribed to notifications for given time
func GetSubscribedChats(time string) ([]chatInfo, error) {
	chats := make([]chatInfo, 0)
	var err error

	switch time {
	case "15m":
		err = db.Db.Select(&chats, getChats15mQuery)
	case "1m":
		err = db.Db.Select(&chats, getChats1mQuery)
	default:
		panic("invalid time: " + time)
	}

	if err != nil {
		return nil, err
	}

	return chats, nil
}

// IsGroupHaveClasses checks if group have classes in near future
// to know if we need to send notifications
func IsGroupHaveClasses(schedule *api2.TimeTableDate, time2 time.Time) (bool, error) {
	// Get first lesson
	if len(schedule.Lessons) == 0 {
		return false, nil
	}
	firstLesson := schedule.Lessons[0]

	// Check if first lesson is actually first lesson
	// Needed because university can add lesson like "приховано з **"
	// Can be removed if it is not the case anymore
	lessonName := strings.ToLower(firstLesson.Periods[0].DisciplineShortName)
	if strings.Contains(lessonName, "приховано") {
		return false, nil
	}

	// Get first lesson call and previous call
	var currentCall api2.CallSchedule
	var previousCall api2.CallSchedule
	for _, call := range calls {
		if call.Number == firstLesson.Number {
			currentCall = call
			break
		}
		previousCall = call
	}

	// Get current call end time and previous call end time
	currentCallEndTime, err := time.Parse("15:04", currentCall.TimeEnd)
	if err != nil {
		return false, err
	}
	currentCallEndTime = time.Date(time2.Year(), time2.Month(), time2.Day(), currentCallEndTime.Hour(), currentCallEndTime.Minute(), 0, 0, location)

	previousCallEndTime, err := time.Parse("15:04", previousCall.TimeEnd)
	if err != nil {
		return false, err
	}
	previousCallEndTime = time.Date(time2.Year(), time2.Month(), time2.Day(), previousCallEndTime.Hour(), previousCallEndTime.Minute(), 0, 0, location)

	// Without this it will not work if first lesson is first lesson of the schedule
	if previousCallEndTime.Equal(currentCallEndTime) {
		previousCallEndTime = time2.Add(-1 * time.Minute)
	}

	// So, to check if group have classes we need to check
	// if current time is between previous call end and current call end
	if time2.After(previousCallEndTime) && time2.Before(currentCallEndTime) {
		return true, nil
	}

	return false, nil
}
