from typing import List, Tuple, Optional, Dict, Any
from .cards import Card, Deck
from .ai import AIPlayer
from colorama import Fore, Style, init
import random
import time

# Initialize colorama
init()

class CardGame:
    """Main game class for the card game."""
    
    def __init__(self):
        self.deck = Deck()
        self.player_hand: List[Card] = []
        self.ai = AIPlayer()
        self.game_over = False
        self.score = {"player": 0, "ai": 0}
    
    def deal_cards(self) -> None:
        """Deal cards to the player and AI."""
        # Split the deck between player and AI
        while not self.deck.is_empty():
            if card := self.deck.draw():
                self.player_hand.append(card)
            if card := self.deck.draw():
                self.ai.add_card(card)
    
    def start_game(self) -> None:
        """Start a new game."""
        print(f"{Fore.CYAN}=== Welcome to the Card Game! ==={Style.RESET_ALL}\n")
        print("You'll be playing against the computer.")
        print("Each turn, you'll play a card, and the higher card wins the round.")
        print("The game continues until one player runs out of cards.\n")
        
        self.deal_cards()
        self.game_loop()
    
    def game_loop(self) -> None:
        """Main game loop."""
        round_num = 1
        
        while not self.game_over:
            print(f"{Fore.YELLOW}\n=== Round {round_num} ==={Style.RESET_ALL}")
            print(f"Your cards: {len(self.player_hand)}")
            print(f"{self.ai.name}'s cards: {len(self.ai.hand)}\n")
            
            # Player's turn
            if not self.player_hand:
                print(f"{Fore.RED}You've run out of cards!{Style.RESET_ALL}")
                self.game_over = True
                break
                
            print("Your cards:")
            for i, card in enumerate(self.player_hand, 1):
                print(f"{i}. {card}")
            
            # Get player's card choice
            while True:
                try:
                    choice = input("\nChoose a card to play (1-{}): ".format(len(self.player_hand)))
                    if not choice.isdigit() or not (1 <= int(choice) <= len(self.player_hand)):
                        raise ValueError("Invalid choice")
                    break
                except ValueError:
                    print(f"{Fore.RED}Please enter a number between 1 and {len(self.player_hand)}{Style.RESET_ALL}")
            
            player_card = self.player_hand.pop(int(choice) - 1)
            
            # AI's turn
            ai_card = self.ai.play_card()
            
            print(f"\n{Fore.GREEN}You played: {player_card}{Style.RESET_ALL}")
            print(f"{Fore.RED}{self.ai.name} played: {ai_card}{Style.RESET_ALL}")
            
            # Determine round winner
            if player_card.rank > ai_card.rank:
                print(f"{Fore.GREEN}You win this round!{Style.RESET_ALL}")
                self.score["player"] += 1
            elif ai_card.rank > player_card.rank:
                print(f"{Fore.RED}{self.ai.name} wins this round!{Style.RESET_ALL}")
                self.score["ai"] += 1
            else:
                print("It's a tie!")
            
            # Check if game over
            if not self.player_hand or not self.ai.has_cards():
                self.game_over = True
            
            round_num += 1
            time.sleep(1.5)  # Pause for readability
        
        self.end_game()
    
    def end_game(self) -> None:
        """Display final score and winner."""
        print("\n" + "="*30)
        print(f"{Fore.CYAN}Game Over!{Style.RESET_ALL}")
        print(f"Final Score - You: {self.score['player']} | {self.ai.name}: {self.score['ai']}")
        
        if self.score["player"] > self.score["ai"]:
            print(f"{Fore.GREEN}Congratulations! You won the game!{Style.RESET_ALL}")
        elif self.score["ai"] > self.score["player"]:
            print(f"{Fore.RED}{self.ai.name} won the game! Better luck next time!{Style.RESET_ALL}")
        else:
            print("The game ended in a tie!")
        
        print("Thanks for playing!")

if __name__ == "__main__":
    game = CardGame()
    game.start_game()
