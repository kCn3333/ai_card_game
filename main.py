#!/usr/bin/env python3
"""
AI Card Game

A simple card game where you play against an AI opponent.
The goal is to win more rounds than the AI by playing higher-ranked cards.
"""

def main():
    """Main function to start the game."""
    from card_game.game import CardGame
    
    while True:
        # Create and start a new game
        game = CardGame()
        game.start_game()
        
        # Ask if the player wants to play again
        play_again = input("\nWould you like to play again? (y/n): ").strip().lower()
        if play_again != 'y':
            print("Thanks for playing! Goodbye!")
            break

if __name__ == "__main__":
    main()
