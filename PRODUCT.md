# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Hiring managers first, arriving from Evan Wilson's resume or LinkedIn and giving the page about a minute; they need to see an AI video data pipeline that decides automatically which clips are fit for a training dataset, and evidence that its decisions are right. ML and data engineers second, who check the rules, thresholds, label accuracy and reproducibility. Desktop and phone viewing are about equal. (Confirmed for the whole portfolio on 2026-10-09.)

## Product Purpose

Clip Curator turns raw video into training-data decisions with no human review. 125 six-second clips are cut from 17 openly licensed source videos; a known defect (blur, bad exposure, frozen, black, low resolution, corrupt, exact and near duplicates) is injected into about a third with a fixed seed. YOLOv8 object detection, CLIP scene labels (few-shot from reference clips) and signal checks (brightness, sharpness, motion, perceptual hashes, file integrity) produce structured data; dbt applies a governed rule set; every clip is accepted or rejected with its reason. Results: 81 accepted (8.1 minutes), 44 of 44 defects rejected, 0 of 81 clean clips wrongly rejected, scene labels 72 of 72 correct few-shot vs 68 of 72 zero-shot, and a second model run reproduces every number byte for byte. The page shows the decisions with the clips themselves.

## Positioning

Data curation as a measured pipeline: rules scored against known answers on every build, the build fails if they slip, and the reader can see every clip and why it was kept or cut.

## Operating Context

Static page with inline data and a thumbnail per clip; built from DuckDB or Snowflake; also published as a Claude artifact and as a product view inside Switchyard.

## Capabilities and Constraints

- Data: 125 clip decisions (source, setting, decision, reasons, duplicate_of, measurements, AI scene and whether it is correct, people, objects, injected defect, outcome), rules with threshold, hits, false alarms, recall and precision, defects caught, accepted composition by setting, label quality by method, object counts, sources with licences, totals, thumbnails.
- Every number comes from data.json.

## Brand Commitments

Each portfolio project has its own visual world and its own new colour palette, distinct from Reprise (cool white, ink, blue ramp, amber), Cloverfield (control-room black, Caltrans orange, green/amber/red), Cloverleaf (concrete grey, plum, lime), Switchyard (cream, rust, umber), Curbside (newsprint, ink, taxi yellow) and the earlier IBM Plex blue and sign-green looks.

## Evidence on Hand

dashboard/data.json with real thumbnails; README results table.

## Product Principles

1. Show the clips: the frames are the evidence.
2. Every decision carries its reason.
3. The scoring against known answers is the headline.
4. Every mark maps to real data.

## Accessibility & Inclusion

WCAG AA contrast in light and dark; decision never carried by colour alone; works at phone width.
