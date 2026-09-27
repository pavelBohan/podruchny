using System;
using System.Text.Json;
using System.Collections.Generic;

namespace PromptValidator
{
    class Program
    {
        static void Main(string[] args)
        {
            if (args.Length == 0)
            {
                Console.WriteLine("{\"error\": \"No input data\"}");
                return;
            }

            try
            {
                // Парсим входящий JSON
                string inputJson = args[0];
                var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                var context = JsonSerializer.Deserialize<Dictionary<string, object>>(inputJson, options);

                // === ЛОГИКА ВАЛИДАЦИИ И ОПТИМИЗАЦИИ ===
                var validated = ValidateAndOptimize(context);

                // Возвращаем результат как JSON
                Console.WriteLine(JsonSerializer.Serialize(validated, options));
            }
            catch (Exception ex)
            {
                Console.WriteLine($"{{\"error\": \"{ex.Message}\"}}");
            }
        }

        static Dictionary<string, object> ValidateAndOptimize(Dictionary<string, object> input)
        {
            var result = new Dictionary<string, object>();

            // Валидация обязательных полей
            foreach (var key in new[] { "subject", "grade", "topic" })
            {
                if (input.ContainsKey(key) && input[key] is string value && !string.IsNullOrWhiteSpace(value))
                {
                    // Очистка и нормализация текста
                    result[key] = value.Trim().Normalize();
                }
                else
                {
                    result[key] = "";
                }
            }

            // Обработка дополнительного контекста
            if (input.ContainsKey("additional_context") && input["additional_context"] is string ctx)
            {
                result["additional_context"] = ctx.Trim().Length > 500 
                    ? ctx.Substring(0, 500) + "..." 
                    : ctx.Trim();
            }
            else
            {
                result["additional_context"] = "";
            }

            // Валидация тона
            var validTones = new[] { "professional", "friendly", "strict", "motivational" };
            if (input.ContainsKey("tone") && input["tone"] is string tone && Array.IndexOf(validTones, tone) >= 0)
            {
                result["tone"] = tone;
            }
            else
            {
                result["tone"] = "professional"; // default
            }

            return result;
        }
    }
}