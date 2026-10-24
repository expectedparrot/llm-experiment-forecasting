#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(ggplot2))

here <- "."
run <- "."
scores <- read.csv(file.path(run, "study_scores.csv"), stringsAsFactors = FALSE)
model_names <- c("gpt-6-astra", "claude-fable-5", "gemini-4-argon")
scores <- scores[scores$model %in% model_names, ]

keys <- c("scenario_id", "study", "outcome_name", "condition_a", "condition_b")
human_twin <- unique(scores[scores$model == "gpt-6-astra",
                            c(keys, "truth_effect_b_minus_a", "archive_gpt4_effect_b_minus_a")])
one_shot <- aggregate(
  one_shot_effect ~ scenario_id + study + outcome_name + condition_a + condition_b,
  data = scores, FUN = mean
)
cases <- merge(human_twin, one_shot, by = keys)
cases <- cases[order(cases$study, cases$truth_effect_b_minus_a, cases$scenario_id), ]
cases$case_id <- paste(cases$study, cases$scenario_id, sep = "::")
counts <- table(cases$study)
cases$rank_by_human_effect <- ave(cases$truth_effect_b_minus_a, cases$study, FUN = seq_along)
cases$contrasts_in_study <- ave(cases$truth_effect_b_minus_a, cases$study, FUN = length)
cases$twin_mae_by_study <- ave(
  abs(cases$archive_gpt4_effect_b_minus_a - cases$truth_effect_b_minus_a),
  cases$study, FUN = mean
)
cases$one_shot_mae_by_study <- ave(
  abs(cases$one_shot_effect - cases$truth_effect_b_minus_a),
  cases$study, FUN = mean
)
cases$winner_by_study <- ifelse(
  cases$one_shot_mae_by_study < cases$twin_mae_by_study, "One-shot",
  ifelse(cases$twin_mae_by_study < cases$one_shot_mae_by_study, "Twins", "Tie")
)
cases$study_panel <- paste0(
  cases$study, " (n=", as.integer(counts[cases$study]), ")",
  ifelse(cases$winner_by_study == "One-shot", " 🏀", "")
)
study_order <- unique(cases$study_panel)
cases$study_panel <- factor(cases$study_panel, levels = study_order)
jitter_half_width <- 0.12
cases$x_jitter <- ifelse(
  cases$contrasts_in_study == 1,
  0,
  -jitter_half_width + 2 * jitter_half_width *
    (cases$rank_by_human_effect - 1) / (cases$contrasts_in_study - 1)
)
case_jitter <- setNames(cases$x_jitter, cases$case_id)

write.csv(cases, file.path(here, "study_grid_plot_data.csv"), row.names = FALSE)

long <- rbind(
  data.frame(case_id = cases$case_id, study_panel = cases$study_panel,
             approach = "Twins", x = 1,
             effect = cases$archive_gpt4_effect_b_minus_a),
  data.frame(case_id = cases$case_id, study_panel = cases$study_panel,
             approach = "Human", x = 2,
             effect = cases$truth_effect_b_minus_a),
  data.frame(case_id = cases$case_id, study_panel = cases$study_panel,
             approach = "One-shot", x = 3,
             effect = cases$one_shot_effect)
)
long$approach <- factor(long$approach, levels = c("Twins", "Human", "One-shot"))
long$x_jittered <- long$x + case_jitter[long$case_id]

segments_twin <- data.frame(
  case_id = cases$case_id, study_panel = cases$study_panel,
  winner = cases$winner_by_study,
  x = 1 + case_jitter[cases$case_id],
  xend = 2 + case_jitter[cases$case_id],
  y = cases$archive_gpt4_effect_b_minus_a,
  yend = cases$truth_effect_b_minus_a,
  linewidth = ifelse(cases$winner_by_study == "Twins", 0.65, 0.22),
  alpha = ifelse(cases$winner_by_study == "Twins", 0.50, 0.15)
)
segments_shot <- data.frame(
  case_id = cases$case_id, study_panel = cases$study_panel,
  winner = cases$winner_by_study,
  x = 2 + case_jitter[cases$case_id],
  xend = 3 + case_jitter[cases$case_id],
  y = cases$truth_effect_b_minus_a,
  yend = cases$one_shot_effect,
  linewidth = ifelse(cases$winner_by_study == "One-shot", 0.65, 0.22),
  alpha = ifelse(cases$winner_by_study == "One-shot", 0.50, 0.15)
)

p <- ggplot(long, aes(x = x_jittered, y = effect, group = case_id)) +
  geom_hline(yintercept = 0, color = "#333333", linewidth = 0.28) +
  geom_segment(data = segments_twin,
               aes(x = x, xend = xend, y = y, yend = yend, group = case_id,
                   linewidth = linewidth, alpha = alpha),
               inherit.aes = FALSE, color = "#C05A3A") +
  geom_segment(data = segments_shot,
               aes(x = x, xend = xend, y = y, yend = yend, group = case_id,
                   linewidth = linewidth, alpha = alpha),
               inherit.aes = FALSE, color = "#286A9B") +
  geom_point(aes(color = approach), alpha = 0.42, size = 0.45) +
  facet_wrap(~study_panel, ncol = 8, scales = "free_y",
             axes = "all_y", axis.labels = "all_y") +
  scale_x_continuous(breaks = 1:3,
                     labels = c("Twin", "Human", "One-shot"),
                     limits = c(0.86, 3.14), expand = expansion(mult = 0)) +
  scale_y_continuous(breaks = function(x) pretty(x, n = 4),
                     labels = function(x) sprintf("%.2f", x),
                     expand = expansion(mult = c(0.05, 0.05))) +
  scale_color_manual(values = c("Twins" = "#C05A3A", "Human" = "#202020", "One-shot" = "#286A9B")) +
  scale_linewidth_identity() +
  scale_alpha_identity() +
  labs(x = NULL, y = "Signed effect (B − A)", color = NULL,
       title = "Study-level slope plots for every experimental contrast",
       subtitle = "Thicker path = lower study MAE; basketball marks one-shot wins; each panel has its own scale") +
  guides(color = guide_legend(nrow = 1, override.aes = list(alpha = 1, size = 2))) +
  theme_bw(base_size = 8) +
  theme(
    legend.position = "top",
    legend.justification = "left",
    legend.text = element_text(size = 8),
    plot.title = element_text(face = "bold", size = 12),
    plot.subtitle = element_text(size = 9, color = "#555555"),
    strip.background = element_rect(fill = "#f1f1f1", color = "#d8d8d8"),
    strip.text = element_text(size = 5.5, face = "bold", margin = margin(2, 1, 2, 1)),
    axis.text.x = element_text(size = 5, color = "#333333", angle = 0, vjust = 0.5),
    axis.text.y = element_text(size = 5, color = "#333333"),
    axis.title.y = element_text(size = 9),
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "#e6e6e6", linewidth = 0.2),
    panel.spacing = grid::unit(0.45, "lines"),
    plot.margin = margin(8, 10, 8, 8)
  )

png_path <- file.path(here, "study_slope_grid.png")
ggsave(png_path, p, width = 16, height = 15,
       dpi = 320, bg = "white", device = ragg::agg_png)

# Embed the emoji-capable raster rendering in a full-size PDF page. The plot
# geometry is generated in ggplot; high-resolution raster preserves the glyph.
grDevices::pdf(file.path(here, "study_slope_grid.pdf"), width = 16, height = 15,
               useDingbats = FALSE, compress = TRUE)
grid::grid.newpage()
grid::grid.raster(png::readPNG(png_path, native = TRUE),
                  width = grid::unit(1, "npc"),
                  height = grid::unit(1, "npc"), interpolate = FALSE)
grDevices::dev.off()
