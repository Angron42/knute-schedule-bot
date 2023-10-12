package utils

import (
	"github.com/cubicbyte/dteubot/internal/data"
	"github.com/cubicbyte/dteubot/internal/dteubot/settings"
	"github.com/cubicbyte/dteubot/internal/i18n"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"github.com/op/go-logging"
	"os"
	"strings"
	"time"
)

var log = logging.MustGetLogger("bot")

// Telegram markdownV2 characters to escape
var escapeCharsMarkdownV2 = []string{
	"_", "\\_",
	"*", "\\*",
	"[", "\\[",
	"]", "\\]",
	"(", "\\(",
	")", "\\)",
	"~", "\\~",
	"`", "\\`",
	">", "\\>",
	"#", "\\#",
	"+", "\\+",
	"-", "\\-",
	"=", "\\=",
	"|", "\\|",
	"{", "\\{",
	"}", "\\}",
	".", "\\.",
	"!", "\\!",
}

// InitDatabaseRecords initializes the database records
// for user and chat from given update.
func InitDatabaseRecords(upd *tgbotapi.Update) error {
	log.Debug("Initializing database records")

	// Check if the chat is in the database
	cm := GetChatDataManager(upd.FromChat().ID)

	exists, err := cm.IsChatExists()
	if err != nil {
		return err
	}
	if !exists {
		if _, err := cm.CreateChatData(); err != nil {
			return err
		}
	}

	if upd.SentFrom() == nil {
		return nil
	}

	// Check if the user is in the database
	um := GetUserDataManager(upd.SentFrom().ID)

	exists, err = um.IsUserExists()
	if err != nil {
		return err
	}
	if !exists {
		userData, err := um.CreateUserData()
		if err != nil {
			return err
		}

		// Update user data
		userData.FirstName = upd.SentFrom().FirstName
		userData.Username = upd.SentFrom().UserName
		err = um.UpdateUserData(userData)
		if err != nil {
			return err
		}
	}

	return nil
}

// GetSettingIcon returns the icon for the setting: ✅ or ❌
func GetSettingIcon(enabled bool) string {
	if enabled {
		return "✅"
	}
	return "❌"
}

// EscapeTelegramMarkdownV2 escapes the Telegram markdownV2 characters
func EscapeTelegramMarkdownV2(str string) string {
	// TODO: Replace this with tgbotapi.EscapeText
	replacer := strings.NewReplacer(escapeCharsMarkdownV2...)
	return replacer.Replace(str)
}

// ParseTime parses time in given layout with local timezone
func ParseTime(layout string, value string) (time.Time, error) {
	return time.ParseInLocation(layout, value, settings.Location)
}

// GetChatDataManager returns ChatDataManager for given chat ID.
func GetChatDataManager(chatId int64) *data.ChatDataManager {
	return &data.ChatDataManager{ChatId: chatId, Database: settings.Db}
}

// GetUserDataManager returns UserDataManager for given user ID.
func GetUserDataManager(userId int64) *data.UserDataManager {
	return &data.UserDataManager{UserId: userId, Database: settings.Db}
}

// GetLang returns the language of the chat.
func GetLang(cm *data.ChatDataManager) (*i18n.Language, error) {
	chatData, err := cm.GetChatData()
	if err != nil {
		return nil, err
	}

	return GetChatLang(chatData)
}

// GetChatLang returns the language of the chat from given ChatData.
func GetChatLang(chatData *data.ChatData) (*i18n.Language, error) {
	// Use default language if chat language is not set
	var langCode string
	if chatData.LanguageCode == "" {
		langCode = os.Getenv("DEFAULT_LANG")
	} else {
		langCode = chatData.LanguageCode
	}

	// Get language
	lang, ok := settings.Languages[langCode]
	if !ok {
		return nil, &i18n.LanguageNotFoundError{LangCode: langCode}
	}

	return &lang, nil
}
